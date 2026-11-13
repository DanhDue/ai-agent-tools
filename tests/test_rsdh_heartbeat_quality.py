"""Tests for hybrid heartbeat estimator and live polyglot quality progress (Task 02).

Covers BDD scenarios RSDH-HP-02, RSDH-HP-03, RSDH-EC-02, RSDH-FR-02, and RSDH-FR-07.
"""

from __future__ import annotations

import importlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
ESTIMATE_SCRIPT = REPO_ROOT / "scripts" / "estimate_heartbeat.py"
QC_SCRIPTS = REPO_ROOT / "skills" / "quality_check" / "resources" / "scripts"
VERIFY_SCRIPT = QC_SCRIPTS / "verify_polyglot_registry.py"


def _load_estimator_module() -> Any:
    """Import scripts/estimate_heartbeat lazily inside test bodies."""
    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return importlib.import_module("estimate_heartbeat")


def _load_verify_module() -> Any:
    """Import verify_polyglot_registry lazily inside test bodies."""
    qc_dir = str(QC_SCRIPTS)
    if qc_dir not in sys.path:
        sys.path.insert(0, qc_dir)
    return importlib.import_module("verify_polyglot_registry")


def _init_git_quality_repo(
    repo_dir: Path, cap_script: str, *, cap_name: str = "slow_check"
) -> tuple[Path, Path]:
    """Create a committed git repository with a python quality provider."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "rsdh@example.com"],
        cwd=repo_dir,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "RSDH Test"],
        cwd=repo_dir,
        check=True,
    )

    cap_file = repo_dir / f"{cap_name}.py"
    cap_file.write_text(cap_script, encoding="utf-8")

    agents_dir = repo_dir / ".agents" / "quality"
    agents_dir.mkdir(parents=True, exist_ok=True)
    registry = {
        "schema_version": 1,
        "providers": [
            {
                "id": "python-core",
                "skill": "d3nexus:python-quality-check",
                "required": True,
                "profiles": ["pr", "epic"],
            }
        ],
    }
    manifest = {
        "schema_version": 1,
        "capabilities": {
            cap_name: [sys.executable, str(cap_file)],
        },
        "profiles": {
            "pr": [cap_name],
            "epic": [cap_name],
        },
    }
    reg_file = agents_dir / "check_quality.json"
    reg_file.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    (agents_dir / "python-quality.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "Init RSDH quality repo"],
        cwd=repo_dir,
        check=True,
    )
    return repo_dir, reg_file


def _wait_for_path(path: Path, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return True
        time.sleep(0.02)
    return path.exists()


def _wait_for_condition(predicate: Any, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return bool(predicate())


def _read_quality_active(repo_dir: Path) -> dict[str, Any]:
    qa_path = repo_dir / ".devtool" / "state" / "quality_active.json"
    if not qa_path.is_file():
        return {}
    try:
        data = json.loads(qa_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def test_rsdh_hp_02_estimator_tiers_cli_and_api(tmp_path: Path) -> None:
    """[RSDH-HP-02] Rule-based estimator maps workloads across light, medium, and heavy tiers."""
    eh = _load_estimator_module()

    # Python API verification
    micro = eh.estimate_workload(tasks_count=1, files_count=1)
    assert micro["estimated_sec"] == 35
    assert micro["tier"] == "light"
    assert micro["recommended_interval_sec"] is None

    wave = eh.estimate_workload(tasks_count=2, files_count=5)
    assert wave["estimated_sec"] == 80
    assert wave["tier"] == "medium"
    assert wave["recommended_interval_sec"] == 180

    full_prof = eh.estimate_workload(quality_profile="full")
    assert full_prof["estimated_sec"] == 250
    assert full_prof["tier"] == "heavy"
    assert full_prof["recommended_interval_sec"] == 240

    e2e_prof = eh.estimate_workload(quality_profile="epic", has_e2e=True)
    assert e2e_prof["estimated_sec"] == 455
    assert e2e_prof["tier"] == "heavy"
    assert e2e_prof["recommended_interval_sec"] == 300

    # Epic-dir + wave inspection on temp task markdowns
    epic_dir = tmp_path / ".devtool" / "epic" / "demo_epic"
    epic_dir.mkdir(parents=True)
    (epic_dir / "task_01_done.md").write_text(
        "---\nid: task_01_done\nstatus: done\nepic: demo_epic\n---\n"
        "# Task 1\n\n## Files\n\nAllowed files:\n- `a.py`\n\n## Dependencies & Blockers\n\nNone.\n",
        encoding="utf-8",
    )
    (epic_dir / "task_02_wave1.md").write_text(
        "---\nid: task_02_wave1\nstatus: todo\nepic: demo_epic\n---\n"
        "# Task 2\n\n## Files\n\nAllowed files:\n- `b.py`\n- `c.py`\n\n## Dependencies & Blockers\n\nNone.\n",
        encoding="utf-8",
    )
    (epic_dir / "task_03_wave2.md").write_text(
        "---\nid: task_03_wave2\nstatus: todo\nepic: demo_epic\n---\n"
        "# Task 3\n\n## Files\n\nAllowed files:\n- `d.py`\n\n"
        "## Dependencies & Blockers\n\nBlocked by [Task 2](task_02_wave1.md).\n",
        encoding="utf-8",
    )
    wave1_est = eh.estimate_workload(epic_dir=epic_dir, wave=1)
    # Wave 1 has 1 pending task (task_02_wave1, since task_01_done is done) and 2 allowed files
    assert wave1_est["tasks_count"] == 1
    assert wave1_est["files_count"] == 2
    assert wave1_est["estimated_sec"] == 5 + 25 * 1 + 5 * 2
    assert wave1_est["tier"] == "light"

    wave2_est = eh.estimate_workload(epic_dir=epic_dir, wave=2)
    assert wave2_est["tasks_count"] == 1
    assert wave2_est["files_count"] == 1
    assert wave2_est["estimated_sec"] == 35

    # CLI verification with --json
    cases = [
        (["--tasks-count", "1", "--files-count", "1", "--json"], 35, "light", None),
        (["--tasks-count", "2", "--files-count", "5", "--json"], 80, "medium", 180),
        (["--quality-profile", "full", "--json"], 250, "heavy", 240),
        (
            ["--quality-profile", "epic", "--has-e2e", "--json"],
            455,
            "heavy",
            300,
        ),
    ]
    for args, exp_sec, exp_tier, exp_interval in cases:
        proc = subprocess.run(
            [sys.executable, str(ESTIMATE_SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["estimated_sec"] == exp_sec
        assert payload["tier"] == exp_tier
        assert payload["recommended_interval_sec"] == exp_interval
        assert isinstance(payload.get("reason"), str) and payload["reason"]


def test_rsdh_ec_02_zero_clamp_and_e2e_escalation() -> None:
    """[RSDH-EC-02] Heartbeat estimator clamps zero/negative inputs and escalates E2E to 300s."""
    eh = _load_estimator_module()

    zero_api = eh.estimate_workload(tasks_count=0, files_count=0)
    assert zero_api["estimated_sec"] == 5
    assert zero_api["tier"] == "light"
    assert zero_api["recommended_interval_sec"] is None

    neg_api = eh.estimate_workload(tasks_count=-4, files_count=-10)
    assert neg_api["estimated_sec"] == 5
    assert neg_api["tier"] == "light"
    assert neg_api["recommended_interval_sec"] is None

    e2e_only = eh.estimate_workload(tasks_count=0, files_count=0, has_e2e=True)
    assert e2e_only["estimated_sec"] == 245
    assert e2e_only["tier"] == "heavy"
    assert e2e_only["recommended_interval_sec"] == 300

    empty_cli = subprocess.run(
        [
            sys.executable,
            str(ESTIMATE_SCRIPT),
            "--tasks-count",
            "0",
            "--files-count",
            "0",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert empty_cli.returncode == 0, empty_cli.stderr
    empty_json = json.loads(empty_cli.stdout)
    assert empty_json["estimated_sec"] == 5
    assert empty_json["tier"] == "light"
    assert empty_json["recommended_interval_sec"] is None

    epic_e2e_cli = subprocess.run(
        [
            sys.executable,
            str(ESTIMATE_SCRIPT),
            "--quality-profile",
            "epic",
            "--has-e2e",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert epic_e2e_cli.returncode == 0, epic_e2e_cli.stderr
    epic_e2e_json = json.loads(epic_e2e_cli.stdout)
    assert epic_e2e_json["tier"] == "heavy"
    assert epic_e2e_json["recommended_interval_sec"] == 300


def test_rsdh_hp_03_live_stderr_and_quality_active(tmp_path: Path) -> None:
    """[RSDH-HP-03] Polyglot quality runner streams stderr heartbeats and isolates concurrent runs."""
    barrier_dir = tmp_path / "barriers"
    barrier_dir.mkdir()
    cap_script = (
        "import os, pathlib, sys, time\n"
        "bdir = pathlib.Path(os.environ['RSDH_BARRIER_DIR'])\n"
        "tag = os.environ['RSDH_RUN_TAG']\n"
        "print(f'CAP_START:{tag}', flush=True)\n"
        "(bdir / f'{tag}_started').write_text(str(os.getpid()), encoding='utf-8')\n"
        "if tag == 'run1':\n"
        "    deadline = time.monotonic() + 8.0\n"
        "    while not (bdir / 'run2_started').exists() and time.monotonic() < deadline:\n"
        "        time.sleep(0.02)\n"
        "    time.sleep(0.25)\n"
        "else:\n"
        "    deadline = time.monotonic() + 8.0\n"
        "    while not (bdir / 'release_run2').exists() and time.monotonic() < deadline:\n"
        "        time.sleep(0.02)\n"
        "print(f'CAP_DONE:{tag}', flush=True)\n"
    )
    repo, reg_file = _init_git_quality_repo(tmp_path / "repo", cap_script)

    env1 = dict(os.environ, RSDH_BARRIER_DIR=str(barrier_dir), RSDH_RUN_TAG="run1")
    env2 = dict(os.environ, RSDH_BARRIER_DIR=str(barrier_dir), RSDH_RUN_TAG="run2")

    cmd = [
        sys.executable,
        str(VERIFY_SCRIPT),
        str(reg_file),
        "--profile",
        "pr",
        "--execute",
        "--compact",
        "--heartbeat-interval",
        "0.08",
        "--epic",
        "demo-sync",
    ]
    p1 = subprocess.Popen(
        cmd,
        cwd=repo,
        env=env1,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    p2 = subprocess.Popen(
        cmd,
        cwd=repo,
        env=env2,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert _wait_for_path(barrier_dir / "run1_started", timeout=8.0)
        assert _wait_for_path(barrier_dir / "run2_started", timeout=8.0)

        # Wait until both concurrent runs appear as "running" under runs[run_id]
        def _both_running() -> bool:
            qa = _read_quality_active(repo)
            runs = qa.get("runs", {})
            running = [
                r
                for r in runs.values()
                if isinstance(r, dict) and r.get("status") == "running"
            ]
            return len(running) == 2

        assert _wait_for_condition(_both_running, timeout=5.0)
        mid_qa = _read_quality_active(repo)
        mid_runs = mid_qa["runs"]
        assert len(mid_runs) == 2
        run_ids_by_pid = {int(r["pid"]): rid for rid, r in mid_runs.items()}
        rid1 = run_ids_by_pid[p1.pid]
        rid2 = run_ids_by_pid[p2.pid]
        assert rid1 != rid2
        for rid, entry in mid_runs.items():
            assert entry["run_id"] == rid
            assert entry["epic_slug"] == "demo-sync"
            assert entry["host"]
            assert entry["updated_at"]
            assert int(entry["ttl_sec"]) >= 120

        # Wait for p1 to finish while p2 is still blocked on release_run2
        out1, err1 = p1.communicate(timeout=10.0)
        assert p1.returncode == 0, out1 + err1
        assert "GATE_PASS: python-core:slow_check" in out1
        assert "[quality_check]" in err1
        assert "python-core:slow_check" in err1
        assert "s elapsed)" in err1

        def _p1_passed_p2_running() -> bool:
            qa = _read_quality_active(repo)
            runs = qa.get("runs", {})
            return (
                runs.get(rid1, {}).get("status") == "passed"
                and runs.get(rid1, {}).get("finished_at") is not None
                and runs.get(rid2, {}).get("status") == "running"
                and runs.get(rid2, {}).get("finished_at") is None
            )

        assert _wait_for_condition(_p1_passed_p2_running, timeout=5.0)

        # Release p2 and verify both finalized cleanly and logs are isolated
        (barrier_dir / "release_run2").write_text("go", encoding="utf-8")
        out2, err2 = p2.communicate(timeout=10.0)
        assert p2.returncode == 0, out2 + err2
        assert "GATE_PASS: python-core:slow_check" in out2
        assert "[quality_check]" in err2

        final_runs = _read_quality_active(repo)["runs"]
        assert final_runs[rid1]["status"] == "passed"
        assert final_runs[rid2]["status"] == "passed"
        assert final_runs[rid1]["finished_at"] is not None
        assert final_runs[rid2]["finished_at"] is not None

        log1 = (
            repo
            / "build"
            / "quality"
            / "python-core"
            / "runs"
            / rid1
            / "slow_check.log"
        )
        log2 = (
            repo
            / "build"
            / "quality"
            / "python-core"
            / "runs"
            / rid2
            / "slow_check.log"
        )
        assert log1.is_file()
        assert log2.is_file()
        txt1 = log1.read_text(encoding="utf-8")
        txt2 = log2.read_text(encoding="utf-8")
        assert "CAP_DONE:run1" in txt1 and "CAP_DONE:run2" not in txt1
        assert "CAP_DONE:run2" in txt2 and "CAP_DONE:run1" not in txt2

        # Python API also accepts heartbeat_interval and epic_slug cleanly
        vpr = _load_verify_module()
        head_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
        (barrier_dir / "release_run2").write_text("go", encoding="utf-8")
        os.environ["RSDH_BARRIER_DIR"] = str(barrier_dir)
        os.environ["RSDH_RUN_TAG"] = "run3"
        try:
            api_res = vpr.verify_polyglot_execution(
                registry_data=json.loads(reg_file.read_text(encoding="utf-8")),
                requested_profile="pr",
                repository_sha=head_sha,
                repo_root=repo,
                execute=True,
                heartbeat_interval=0.05,
                epic_slug="demo-sync",
            )
            assert api_res["status"] == "PASS"
        finally:
            os.environ.pop("RSDH_BARRIER_DIR", None)
            os.environ.pop("RSDH_RUN_TAG", None)
    finally:
        (barrier_dir / "release_run2").write_text("cleanup", encoding="utf-8")
        for proc in (p1, p2):
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)


class Test_Polyglot_Integration:
    """Tier C integration suite for live polyglot runner concurrency and signal safety."""

    def test_rsdh_hp_03_integration_worktree_dual_root(self, tmp_path: Path) -> None:
        """[RSDH-HP-03] Concurrent worktree runner mirrors quality_active.json to primary root."""
        primary_repo = tmp_path / "primary_repo"
        cap_script = (
            "import os, pathlib, time\n"
            "bdir = pathlib.Path(os.environ['RSDH_BARRIER_DIR'])\n"
            "tag = os.environ['RSDH_RUN_TAG']\n"
            "(bdir / f'{tag}_started').write_text(str(os.getpid()), encoding='utf-8')\n"
            "deadline = time.monotonic() + 8.0\n"
            "while not (bdir / 'release_wt').exists() and time.monotonic() < deadline:\n"
            "    time.sleep(0.02)\n"
            "print(f'WT_DONE:{tag}', flush=True)\n"
        )
        _, _ = _init_git_quality_repo(primary_repo, cap_script)
        wt_dir = tmp_path / "wt_slot"
        subprocess.run(
            ["git", "worktree", "add", "-q", "-b", "epic/wt-demo", str(wt_dir)],
            cwd=primary_repo,
            check=True,
        )
        wt_reg = wt_dir / ".agents" / "quality" / "check_quality.json"
        barrier_dir = tmp_path / "wt_barriers"
        barrier_dir.mkdir()
        env_wt = dict(os.environ, RSDH_BARRIER_DIR=str(barrier_dir), RSDH_RUN_TAG="wt1")
        p_wt = subprocess.Popen(
            [
                sys.executable,
                str(VERIFY_SCRIPT),
                str(wt_reg),
                "--profile",
                "pr",
                "--execute",
                "--compact",
                "--heartbeat-interval",
                "0.08",
            ],
            cwd=wt_dir,
            env=env_wt,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            assert _wait_for_path(barrier_dir / "wt1_started", timeout=8.0)

            def _mirrored_running() -> bool:
                p_qa = _read_quality_active(primary_repo)
                w_qa = _read_quality_active(wt_dir)
                runs = p_qa.get("runs", {})
                if not runs:
                    return False
                first_run = next(iter(runs.values()))
                return (
                    float(first_run.get("elapsed_sec", 0.0)) >= 0.08
                    and p_qa.get("generation") == w_qa.get("generation")
                    and p_qa.get("runs") == w_qa.get("runs")
                )

            assert _wait_for_condition(_mirrored_running, timeout=5.0)
            p_qa = _read_quality_active(primary_repo)
            run_entry = next(iter(p_qa["runs"].values()))
            assert run_entry["epic_slug"] == "wt-demo"
            assert run_entry["status"] == "running"

            (barrier_dir / "release_wt").write_text("go", encoding="utf-8")
            out_wt, err_wt = p_wt.communicate(timeout=10.0)
            assert p_wt.returncode == 0, out_wt + err_wt
            assert "[quality_check]" in err_wt

            p_final = _read_quality_active(primary_repo)
            w_final = _read_quality_active(wt_dir)
            assert p_final["generation"] == w_final["generation"]
            final_entry = next(iter(p_final["runs"].values()))
            assert final_entry["status"] == "passed"
            assert final_entry["finished_at"] is not None
        finally:
            (barrier_dir / "release_wt").write_text("cleanup", encoding="utf-8")
            if p_wt.poll() is None:
                p_wt.kill()
                p_wt.wait(timeout=5)
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt_dir)],
                cwd=primary_repo,
                check=False,
                capture_output=True,
            )

    def test_rsdh_fr_02_failing_run_preserves_sibling_live_run(
        self, tmp_path: Path
    ) -> None:
        """[RSDH-FR-02] Failing capability run finalizes only its run_id without clobbering sibling."""
        barrier_dir = tmp_path / "barriers"
        barrier_dir.mkdir()
        cap_script = (
            "import os, pathlib, sys, time\n"
            "bdir = pathlib.Path(os.environ['RSDH_BARRIER_DIR'])\n"
            "tag = os.environ['RSDH_RUN_TAG']\n"
            "(bdir / f'{tag}_started').write_text(str(os.getpid()), encoding='utf-8')\n"
            "if tag == 'fail1':\n"
            "    deadline = time.monotonic() + 8.0\n"
            "    while not (bdir / 'healthy2_started').exists() and time.monotonic() < deadline:\n"
            "        time.sleep(0.02)\n"
            "    print('fatal defect occurred', file=sys.stderr, flush=True)\n"
            "    sys.exit(1)\n"
            "else:\n"
            "    deadline = time.monotonic() + 8.0\n"
            "    while not (bdir / 'release_healthy2').exists() and time.monotonic() < deadline:\n"
            "        time.sleep(0.02)\n"
            "    print('healthy run ok', flush=True)\n"
        )
        repo, reg_file = _init_git_quality_repo(tmp_path / "repo", cap_script)

        env_fail = dict(
            os.environ, RSDH_BARRIER_DIR=str(barrier_dir), RSDH_RUN_TAG="fail1"
        )
        env_ok = dict(
            os.environ, RSDH_BARRIER_DIR=str(barrier_dir), RSDH_RUN_TAG="healthy2"
        )

        cmd = [
            sys.executable,
            str(VERIFY_SCRIPT),
            str(reg_file),
            "--profile",
            "pr",
            "--execute",
            "--compact",
            "--heartbeat-interval",
            "0.08",
            "--epic",
            "fail-isolation",
        ]
        p_ok = subprocess.Popen(
            cmd,
            cwd=repo,
            env=env_ok,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        p_fail = subprocess.Popen(
            cmd,
            cwd=repo,
            env=env_fail,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            assert _wait_for_path(barrier_dir / "healthy2_started", timeout=8.0)
            assert _wait_for_path(barrier_dir / "fail1_started", timeout=8.0)

            out_fail, err_fail = p_fail.communicate(timeout=10.0)
            assert p_fail.returncode == 1
            assert "GATE_FAIL: python-core:slow_check" in out_fail

            qa_after_fail = _read_quality_active(repo)
            runs = qa_after_fail.get("runs", {})
            by_pid = {int(r["pid"]): r for r in runs.values()}
            assert by_pid[p_fail.pid]["status"] == "failed"
            assert by_pid[p_fail.pid]["finished_at"] is not None
            assert by_pid[p_ok.pid]["status"] == "running"
            assert by_pid[p_ok.pid]["finished_at"] is None

            (barrier_dir / "release_healthy2").write_text("go", encoding="utf-8")
            out_ok, err_ok = p_ok.communicate(timeout=10.0)
            assert p_ok.returncode == 0, out_ok + err_ok

            final_runs = _read_quality_active(repo)["runs"]
            final_by_pid = {int(r["pid"]): r for r in final_runs.values()}
            assert final_by_pid[p_fail.pid]["status"] == "failed"
            assert final_by_pid[p_ok.pid]["status"] == "passed"
        finally:
            (barrier_dir / "release_healthy2").write_text("cleanup", encoding="utf-8")
            for proc in (p_fail, p_ok):
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=5)

    def test_rsdh_fr_07_signal_abort_reaps_children_and_preserves_sibling(
        self,
        tmp_path: Path,
    ) -> None:
        """[RSDH-FR-07] SIGTERM reaps active child process group and marks only own run aborted."""
        barrier_dir = tmp_path / "barriers"
        barrier_dir.mkdir()
        cap_script = (
            "import os, pathlib, subprocess, sys, time\n"
            "bdir = pathlib.Path(os.environ['RSDH_BARRIER_DIR'])\n"
            "tag = os.environ['RSDH_RUN_TAG']\n"
            "if tag == 'victim':\n"
            "    grand = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
            "    (bdir / 'victim_child.pid').write_text(str(os.getpid()), encoding='utf-8')\n"
            "    (bdir / 'victim_grandchild.pid').write_text(str(grand.pid), encoding='utf-8')\n"
            "    (bdir / 'victim_started').write_text('1', encoding='utf-8')\n"
            "    grand.wait()\n"
            "else:\n"
            "    (bdir / 'sibling_started').write_text(str(os.getpid()), encoding='utf-8')\n"
            "    deadline = time.monotonic() + 10.0\n"
            "    while not (bdir / 'release_sibling').exists() and time.monotonic() < deadline:\n"
            "        time.sleep(0.02)\n"
        )
        repo, reg_file = _init_git_quality_repo(tmp_path / "repo", cap_script)

        env_victim = dict(
            os.environ, RSDH_BARRIER_DIR=str(barrier_dir), RSDH_RUN_TAG="victim"
        )
        env_sibling = dict(
            os.environ, RSDH_BARRIER_DIR=str(barrier_dir), RSDH_RUN_TAG="sibling"
        )

        cmd = [
            sys.executable,
            str(VERIFY_SCRIPT),
            str(reg_file),
            "--profile",
            "pr",
            "--execute",
            "--compact",
            "--heartbeat-interval",
            "0.08",
            "--epic",
            "abort-test",
        ]
        p_sibling = subprocess.Popen(
            cmd,
            cwd=repo,
            env=env_sibling,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        p_victim = subprocess.Popen(
            cmd,
            cwd=repo,
            env=env_victim,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            assert _wait_for_path(barrier_dir / "victim_started", timeout=8.0)
            assert _wait_for_path(barrier_dir / "sibling_started", timeout=8.0)

            def _both_registered() -> bool:
                runs = _read_quality_active(repo).get("runs", {})
                pids = {int(r["pid"]) for r in runs.values() if isinstance(r, dict)}
                return p_victim.pid in pids and p_sibling.pid in pids

            assert _wait_for_condition(_both_registered, timeout=5.0)

            child_pid = int(
                (barrier_dir / "victim_child.pid").read_text(encoding="utf-8").strip()
            )
            grandchild_pid = int(
                (barrier_dir / "victim_grandchild.pid")
                .read_text(encoding="utf-8")
                .strip()
            )
            assert _pid_alive(child_pid)
            assert _pid_alive(grandchild_pid)

            # Interrupt victim runner with SIGTERM
            p_victim.send_signal(signal.SIGTERM)
            p_victim.communicate(timeout=8.0)
            assert p_victim.returncode != 0

            # Active child process group (capability child + grandchild) must be terminated and reaped
            assert _wait_for_condition(lambda: not _pid_alive(child_pid), timeout=3.0)
            assert _wait_for_condition(
                lambda: not _pid_alive(grandchild_pid), timeout=3.0
            )

            # Only victim's run_id transitions to aborted; sibling stays running
            runs_after_abort = _read_quality_active(repo).get("runs", {})
            by_pid = {int(r["pid"]): r for r in runs_after_abort.values()}
            assert by_pid[p_victim.pid]["status"] == "aborted"
            assert by_pid[p_victim.pid]["finished_at"] is not None
            assert by_pid[p_sibling.pid]["status"] == "running"
            assert by_pid[p_sibling.pid]["finished_at"] is None

            # Release healthy sibling and verify it passes cleanly
            (barrier_dir / "release_sibling").write_text("go", encoding="utf-8")
            out_sib, err_sib = p_sibling.communicate(timeout=10.0)
            assert p_sibling.returncode == 0, out_sib + err_sib
            final_by_pid = {
                int(r["pid"]): r for r in _read_quality_active(repo)["runs"].values()
            }
            assert final_by_pid[p_victim.pid]["status"] == "aborted"
            assert final_by_pid[p_sibling.pid]["status"] == "passed"
        finally:
            (barrier_dir / "release_sibling").write_text("cleanup", encoding="utf-8")
            for pid_file in (
                barrier_dir / "victim_child.pid",
                barrier_dir / "victim_grandchild.pid",
            ):
                if pid_file.is_file():
                    try:
                        pid = int(pid_file.read_text(encoding="utf-8").strip())
                        if _pid_alive(pid):
                            os.kill(pid, signal.SIGKILL)
                    except (ValueError, OSError):
                        pass
            for proc in (p_victim, p_sibling):
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=5)
