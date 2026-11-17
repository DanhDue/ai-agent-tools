"""Tests for the agy profile pool, global lease file, quota evaluation, and exhaustion reporting.

Covers BDD Scenarios:
- FPG-HP-11: Pool acquisition picks the first usable profile by priority and records why the others were skipped
- FPG-EC-07: Invalid pool changes are rejected and a launch without the ag_run helpers starts nothing
- FPG-ST-07: A lease is kept alive by heartbeats and reclaimed when it goes stale
- FPG-AR-06: Concurrent orchestrators never share a profile and never lose lease-file updates
- FPG-FR-07: An exhausted pool yields a report that tells the Human how to continue, and a top-up recovers it
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
POOL_SCRIPT = REPO_ROOT / "scripts" / "agy_profile_pool.py"
PERSONA_CONFIG_SCRIPT = REPO_ROOT / "scripts" / "persona_config.py"
DEV_CONFIG_SCRIPT = REPO_ROOT / "scripts" / "dev_config.py"


def _load_module(name: str, path: Path) -> ModuleType:
    """Load a module by path via importlib so RED phase fails as a test failure."""
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    if not path.is_file():
        pytest.fail(f"Expected module does not exist yet: {path}")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        pytest.fail(f"Failed to create module spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _pool_mod() -> ModuleType:
    return _load_module("agy_profile_pool", POOL_SCRIPT)


def _persona_mod() -> ModuleType:
    return _load_module("persona_config", PERSONA_CONFIG_SCRIPT)


def _dev_config_mod() -> ModuleType:
    return _load_module("dev_config", DEV_CONFIG_SCRIPT)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _make_profile_dirs(real_home: Path, names: tuple[str, ...]) -> None:
    homes = real_home / "antigravity_homes"
    homes.mkdir(parents=True, exist_ok=True)
    for name in names:
        (homes / name).mkdir(parents=True, exist_ok=True)


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _subproc_env(
    real_home: Path,
    *,
    home: Path | None = None,
    path_dir: Path | None = None,
    agy_profile: str | None = None,
) -> dict[str, str]:
    env = dict(os.environ)
    env["REAL_HOME"] = str(real_home)
    env["HOME"] = str(home if home is not None else real_home)
    env.pop("AGY_PROFILE", None)
    env.pop("ANTIGRAVITY_PROFILE", None)
    env.pop("TMPDIR", None)
    if agy_profile is not None:
        env["AGY_PROFILE"] = agy_profile
    if path_dir is not None:
        env["PATH"] = f"{path_dir}:{env.get('PATH', '')}"
    return env


def test_fpg_hp_11_pool_selection_priority_and_skip_reasons(tmp_path: Path) -> None:
    """FPG-HP-11: Pool acquisition picks the first usable profile by priority and records skip reasons."""
    pool_mod = _pool_mod()
    real_home = tmp_path / "real_home"
    _make_profile_dirs(real_home, ("p1", "p2", "p3", "p4", "p5", "p6"))
    now = datetime(2026, 11, 17, 10, 0, 0, tzinfo=timezone.utc)

    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": "p6", "priority": 6},
                {"profile": "p2", "priority": 2},
                {"profile": "p1", "priority": 1},
                {"profile": "p4", "priority": 4},
                {"profile": "p3", "priority": 3},
                {"profile": "p5", "priority": 5},
            ],
            "lease_ttl_seconds": 180,
            "heartbeat_seconds": 30,
            "exhausted_recheck_seconds": 600,
            "agy_extra_args": [],
        },
    )

    _write_json(
        real_home / ".d3nexus" / "agy_profile_leases.json",
        {
            "schema_version": 1,
            "profiles": {
                "p2": {
                    "leases": [
                        {
                            "owner_id": "other-orch-1",
                            "repo": "r1",
                            "epic": "e0",
                            "task": "t0",
                            "slot": 1,
                            "role": "orchestrator",
                            "launch": "ag_run",
                            "pid": os.getpid(),
                            "host": socket.gethostname(),
                            "acquired_at": _iso_utc(now - timedelta(seconds=30)),
                            "heartbeat_at": _iso_utc(now - timedelta(seconds=10)),
                        }
                    ],
                    "exhausted_until": None,
                    "exhausted_checked_at": None,
                    "exhausted_reason": None,
                    "quota": None,
                },
                "p3": {
                    "leases": [],
                    "exhausted_until": _iso_utc(now + timedelta(hours=1)),
                    "exhausted_checked_at": None,
                    "exhausted_reason": "5h",
                    "quota": None,
                },
            },
        },
    )

    quotas = {
        "p1": (0.10, "2026-11-17T12:00:00Z", 0.50, "2026-11-22T00:00:00Z"),
        "p2": (0.50, "2026-11-17T12:10:00Z", 0.50, "2026-11-22T00:00:00Z"),
        "p3": (0.60, "2026-11-17T12:20:00Z", 0.50, "2026-11-22T00:00:00Z"),
        "p4": (0.70, "2026-11-17T12:30:00Z", 0.50, "2026-11-22T00:00:00Z"),
        "p5": (0.90, "2026-11-17T12:40:00Z", 0.01, "2026-11-21T08:00:00Z"),
        "p6": (0.90, "2026-11-17T12:50:00Z", 0.50, "2026-11-22T00:00:00Z"),
    }

    def fetcher(profile: str) -> dict[str, Any]:
        f5, r5, fw, rw = quotas[profile]
        return {
            "status": "ACTIVE",
            "email": f"{profile}@example.invalid",
            "gemini5h": {"fraction": f5, "resetTime": r5},
            "geminiWeekly": {"fraction": fw, "resetTime": rw},
            "argonWeekly": {"fraction": 0.5, "resetTime": rw},
        }

    thresholds = {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "agy_argon_min_fraction": 0.10,
    }
    owner = {
        "repo": "ai-agent-tools",
        "epic": "e1",
        "task": "t1",
        "slot": 1,
        "role": "orchestrator",
    }

    acq = pool_mod.acquire(
        owner,
        real_home=real_home,
        host_profile="px",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=fetcher,
        resident_probe=lambda p: p == "p4",
        wait_seconds=0,
        now=now,
    )
    assert acq.profile == "p6"
    assert acq.via_ag_run is True
    assert acq.reason is None
    assert acq.skipped == {
        "p1": "quota",
        "p2": "leased",
        "p3": "exhausted",
        "p4": "resident_process",
        "p5": "quota",
    }

    leases_raw = (real_home / ".d3nexus" / "agy_profile_leases.json").read_text(
        encoding="utf-8"
    )
    assert "@example.invalid" not in leases_raw
    leases_doc = json.loads(leases_raw)
    assert leases_doc["profiles"]["p1"]["exhausted_until"] == "2026-11-17T12:00:00Z"
    assert leases_doc["profiles"]["p1"]["exhausted_reason"] == "5h"
    assert leases_doc["profiles"]["p5"]["exhausted_until"] == "2026-11-21T08:00:00Z"
    assert leases_doc["profiles"]["p5"]["exhausted_reason"] == "weekly"

    # Release and re-acquire when host profile IS p6 -> direct launch (via_ag_run=False)
    pool_mod.release(acq.owner_id, real_home=real_home, now=now)
    acq2 = pool_mod.acquire(
        owner,
        real_home=real_home,
        host_profile="p6",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=fetcher,
        resident_probe=lambda p: p in ("p4", "p6"),
        wait_seconds=0,
        now=now,
    )
    assert acq2.profile == "p6"
    assert acq2.via_ag_run is False
    pool_mod.release(acq2.owner_id, real_home=real_home, now=now)


@pytest.mark.parametrize(
    ("quota_pool", "payload", "expected_ok", "expected_windows"),
    [
        # 5h exact boundary passes; weekly above boundary passes
        (
            "gemini5h",
            {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.15, "resetTime": "2026-11-17T12:00:00Z"},
                "geminiWeekly": {
                    "fraction": 0.021,
                    "resetTime": "2026-11-21T00:00:00Z",
                },
            },
            True,
            [],
        ),
        # weekly exact boundary FAILS (strictly greater > 0.02 required)
        (
            "gemini5h",
            {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.90, "resetTime": "2026-11-17T12:00:00Z"},
                "geminiWeekly": {"fraction": 0.02, "resetTime": "2026-11-21T00:00:00Z"},
            },
            False,
            ["weekly"],
        ),
        # both fail
        (
            "gemini5h",
            {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.149, "resetTime": "2026-11-17T12:00:00Z"},
                "geminiWeekly": {"fraction": 0.02, "resetTime": "2026-11-21T00:00:00Z"},
            },
            False,
            ["5h", "weekly"],
        ),
        # missing geminiWeekly passes as unknown
        (
            "gemini5h",
            {"status": "ACTIVE", "gemini5h": {"fraction": 0.15}, "unavailable": True},
            True,
            [],
        ),
        # empty payload passes
        ("gemini5h", {}, True, []),
        # unavailable & countdown ignored when fraction is present
        (
            "gemini5h",
            {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.80, "unavailable": True, "countdown": "0m"},
                "geminiWeekly": {
                    "fraction": 0.50,
                    "unavailable": True,
                    "countdown": "0m",
                },
            },
            True,
            [],
        ),
        # argonWeekly exact boundary passes; below fails
        (
            "argonWeekly",
            {
                "status": "ACTIVE",
                "argonWeekly": {"fraction": 0.10, "resetTime": "2026-11-21T00:00:00Z"},
            },
            True,
            [],
        ),
        (
            "argonWeekly",
            {
                "status": "ACTIVE",
                "argonWeekly": {"fraction": 0.09, "resetTime": "2026-11-21T00:00:00Z"},
            },
            False,
            ["argonWeekly"],
        ),
    ],
)
def test_fpg_hp_11_evaluate_agy_quota_boundaries(
    quota_pool: str,
    payload: dict[str, Any],
    expected_ok: bool,
    expected_windows: list[str],
) -> None:
    """FPG-HP-11: evaluate_agy_quota enforces 5h >= and weekly > boundaries accurately."""
    pool_mod = _pool_mod()
    thresholds = {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "agy_argon_min_fraction": 0.10,
    }
    verdict = pool_mod.evaluate_agy_quota(payload, quota_pool, thresholds)
    assert verdict.sufficient is expected_ok
    assert [item["window"] for item in verdict.failing] == expected_windows


def test_fpg_hp_11_direct_vs_ag_run_capacity_and_status_skip(tmp_path: Path) -> None:
    """FPG-HP-11: direct leases respect max_concurrent, ag_run requires exclusive profile, and non-ACTIVE skips."""
    pool_mod = _pool_mod()
    real_home = tmp_path / "real_home"
    _make_profile_dirs(real_home, ("p1", "p2"))
    now = datetime(2026, 11, 17, 10, 0, 0, tzinfo=timezone.utc)
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": "p1", "priority": 1, "max_concurrent": 2},
                {"profile": "p2", "priority": 2, "max_concurrent": 2},
            ],
            "lease_ttl_seconds": 180,
            "heartbeat_seconds": 30,
            "exhausted_recheck_seconds": 600,
            "agy_extra_args": [],
        },
    )
    thresholds = {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "agy_argon_min_fraction": 0.10,
    }

    def fetcher(profile: str) -> dict[str, Any]:
        if profile == "p1":
            return {"status": "DISABLED"}
        return {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.8, "resetTime": "2026-11-17T13:00:00Z"},
            "geminiWeekly": {"fraction": 0.8, "resetTime": "2026-11-22T00:00:00Z"},
        }

    # p1 returns DISABLED -> skipped as status:DISABLED, p2 acquired as direct
    o1 = {"repo": "r", "epic": "e", "task": "t1", "slot": 1, "role": "orchestrator"}
    o2 = {"repo": "r", "epic": "e", "task": "t2", "slot": 2, "role": "orchestrator"}
    o3 = {"repo": "r", "epic": "e", "task": "t3", "slot": 3, "role": "orchestrator"}

    a1 = pool_mod.acquire(
        o1,
        real_home=real_home,
        host_profile="p2",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=fetcher,
        resident_probe=lambda _p: False,
        now=now,
    )
    assert a1.profile == "p2"
    assert a1.via_ag_run is False
    assert a1.skipped == {"p1": "status:DISABLED"}

    leases_doc = json.loads(
        (real_home / ".d3nexus" / "agy_profile_leases.json").read_text(encoding="utf-8")
    )
    assert leases_doc["profiles"]["p1"]["exhausted_reason"] == "status:DISABLED"

    # Second direct lease on p2 succeeds (max_concurrent=2)
    a2 = pool_mod.acquire(
        o2,
        real_home=real_home,
        host_profile="p2",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=fetcher,
        resident_probe=lambda _p: False,
        now=now,
    )
    assert a2.profile == "p2"
    assert a2.via_ag_run is False

    # Third direct lease on p2 is refused (at max_concurrent) -> busy
    a3 = pool_mod.acquire(
        o3,
        real_home=real_home,
        host_profile="p2",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=fetcher,
        resident_probe=lambda _p: False,
        now=now,
    )
    assert a3.profile is None
    assert a3.reason == "pool_busy"
    assert a3.skipped == {"p1": "exhausted", "p2": "leased"}

    # ag_run caller also refused on p2 while direct leases exist
    a_ag = pool_mod.acquire(
        o3,
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=fetcher,
        resident_probe=lambda _p: False,
        now=now,
    )
    assert a_ag.profile is None
    assert a_ag.reason == "pool_busy"

    pool_mod.release(a1.owner_id, real_home=real_home, now=now)
    pool_mod.release(a2.owner_id, real_home=real_home, now=now)


def test_fpg_ec_07_invalid_pool_use_is_rejected(tmp_path: Path) -> None:
    """FPG-EC-07: Invalid pool additions, schema violations, and live-lease removals are rejected."""
    pool_mod = _pool_mod()
    _dev_config_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    project.mkdir()
    homes = real_home / "antigravity_homes"
    (homes / "real_p").mkdir(parents=True)
    target_outside = tmp_path / "outside_dir"
    target_outside.mkdir()
    (homes / "link_p").symlink_to(target_outside)

    env = _subproc_env(real_home)
    for args, expected_substr in [
        (["profiles", "add", "ghost"], "ghost"),
        (["profiles", "add", "link_p"], "link_p"),
        (["profiles", "add", "bad name"], "bad name"),
        (["profiles", "add", "real_p", "--priority", "0"], "0"),
    ]:
        proc = subprocess.run(
            [
                sys.executable,
                str(DEV_CONFIG_SCRIPT),
                "--project-root",
                str(project),
                *args,
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 1
        assert expected_substr in (proc.stdout + proc.stderr)

    # First add succeeds
    ok_proc = subprocess.run(
        [
            sys.executable,
            str(DEV_CONFIG_SCRIPT),
            "--project-root",
            str(project),
            "profiles",
            "add",
            "real_p",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok_proc.returncode == 0

    # Second add fails with "already"
    dup_proc = subprocess.run(
        [
            sys.executable,
            str(DEV_CONFIG_SCRIPT),
            "--project-root",
            str(project),
            "profiles",
            "add",
            "real_p",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert dup_proc.returncode == 1
    assert "already" in (dup_proc.stdout + dup_proc.stderr).lower()

    pool_cfg = json.loads(
        (real_home / ".d3nexus" / "agy_profiles.json").read_text(encoding="utf-8")
    )
    assert [entry["profile"] for entry in pool_cfg["pool"]] == ["real_p"]

    # Acquire a live lease on real_p and try to remove -> exits 1 naming lease owner, lease file unchanged.
    # The `profiles remove` subprocess reads the real clock, so the lease time comes from the real clock too.
    now = datetime.now(timezone.utc).replace(microsecond=0)
    thresholds = {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "agy_argon_min_fraction": 0.10,
    }
    acq = pool_mod.acquire(
        {
            "repo": "r1",
            "epic": "epic_lock",
            "task": "t1",
            "slot": 1,
            "role": "orchestrator",
        },
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=lambda _p: {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.9},
            "geminiWeekly": {"fraction": 0.9},
        },
        resident_probe=lambda _p: False,
        now=now,
    )
    assert acq.profile == "real_p"
    before_leases = (real_home / ".d3nexus" / "agy_profile_leases.json").read_bytes()

    rm_proc = subprocess.run(
        [
            sys.executable,
            str(DEV_CONFIG_SCRIPT),
            "--project-root",
            str(project),
            "profiles",
            "remove",
            "real_p",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert rm_proc.returncode == 1
    rm_err = rm_proc.stdout + rm_proc.stderr
    assert acq.owner_id in rm_err or "epic_lock" in rm_err
    assert (
        real_home / ".d3nexus" / "agy_profile_leases.json"
    ).read_bytes() == before_leases

    pool_mod.release(acq.owner_id, real_home=real_home, now=now)

    # Corrupt schema checks: wrong schema_version, unknown key, wrong type
    for bad_cfg, bad_tok in [
        ({"schema_version": 99, "pool": []}, "99"),
        ({"schema_version": 1, "pool": [], "unexpected_key": 1}, "unexpected_key"),
        (
            {"schema_version": 1, "pool": [], "lease_ttl_seconds": "bad"},
            "lease_ttl_seconds",
        ),
    ]:
        bad_home = tmp_path / f"bad_{bad_tok}"
        _write_json(bad_home / ".d3nexus" / "agy_profiles.json", bad_cfg)
        with pytest.raises(ValueError) as exc_info:
            pool_mod.load_pool_config(real_home=bad_home)
        assert bad_tok in str(exc_info.value)


def test_fpg_st_07_lease_lifecycle_heartbeat_and_stale_reclaim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FPG-ST-07: Heartbeats keep a lease live, dead local PIDs or expired TTLs are reclaimed, remote PIDs expire by age only."""
    pool_mod = _pool_mod()
    real_home = tmp_path / "real_home"
    _make_profile_dirs(real_home, ("p1",))
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [{"profile": "p1", "priority": 1}],
            "lease_ttl_seconds": 180,
            "heartbeat_seconds": 30,
            "exhausted_recheck_seconds": 600,
            "agy_extra_args": [],
        },
    )
    thresholds = {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "agy_argon_min_fraction": 0.10,
    }
    healthy = lambda _p: {
        "status": "ACTIVE",
        "gemini5h": {"fraction": 0.9},
        "geminiWeekly": {"fraction": 0.9},
    }

    monkeypatch.setattr(socket, "gethostname", lambda: "h1")
    t_1000 = datetime(2026, 11, 17, 10, 0, 0, tzinfo=timezone.utc)
    t_1002 = datetime(2026, 11, 17, 10, 2, 0, tzinfo=timezone.utc)
    t_1004_30 = datetime(2026, 11, 17, 10, 4, 30, tzinfo=timezone.utc)
    t_1005_30 = datetime(2026, 11, 17, 10, 5, 30, tzinfo=timezone.utc)

    a1 = pool_mod.acquire(
        {
            "owner_id": "o1",
            "epic": "e1",
            "task": "t1",
            "slot": 1,
            "role": "orchestrator",
            "host": "h1",
            "pid": os.getpid(),
        },
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=healthy,
        resident_probe=lambda _p: False,
        now=t_1000,
    )
    assert a1.profile == "p1"

    assert pool_mod.heartbeat("o1", real_home=real_home, now=t_1002) is True

    # At 10:04:30 (150s after 10:02 heartbeat < 180s TTL), lease is live
    st_live = pool_mod.pool_status(real_home=real_home, now=t_1004_30)
    assert st_live["state"] == "busy"
    assert len(st_live["profiles"][0]["leased_by"]) == 1

    # At 10:05:30 (210s after 10:02 > 180s TTL), lease is stale and o2 acquires p1
    st_stale = pool_mod.pool_status(real_home=real_home, now=t_1005_30)
    assert st_stale["state"] == "ok"
    assert st_stale["profiles"][0]["leased_by"] == []

    a2 = pool_mod.acquire(
        {
            "owner_id": "o2",
            "epic": "e2",
            "task": "t2",
            "slot": 1,
            "role": "orchestrator",
            "host": "h1",
            "pid": os.getpid(),
        },
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=healthy,
        resident_probe=lambda _p: False,
        now=t_1005_30,
    )
    assert a2.profile == "p1"

    # Release o2 twice: first removes, second is a no-op
    assert pool_mod.release("o2", real_home=real_home, now=t_1005_30) is True
    after_first = (real_home / ".d3nexus" / "agy_profile_leases.json").read_bytes()
    assert pool_mod.release("o2", real_home=real_home, now=t_1005_30) is False
    assert (
        real_home / ".d3nexus" / "agy_profile_leases.json"
    ).read_bytes() == after_first

    # Dead PID on same host h1 is stale 5s after last heartbeat; same dead PID on another host h2 stays live until TTL
    dead_proc = subprocess.Popen([sys.executable, "-c", "pass"])
    dead_proc.wait(timeout=10)
    dead_pid = dead_proc.pid

    a_dead = pool_mod.acquire(
        {
            "owner_id": "o_dead",
            "epic": "e3",
            "task": "t3",
            "slot": 1,
            "role": "orchestrator",
            "host": "h1",
            "pid": dead_pid,
        },
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=healthy,
        resident_probe=lambda _p: False,
        now=t_1000,
    )
    assert a_dead.profile == "p1"

    t_1000_05 = t_1000 + timedelta(seconds=5)
    # From host h2 (another host), dead PID is stale by age only -> still live at +5s
    monkeypatch.setattr(socket, "gethostname", lambda: "h2")
    st_remote = pool_mod.pool_status(real_home=real_home, now=t_1000_05)
    assert st_remote["state"] == "busy"
    assert len(st_remote["profiles"][0]["leased_by"]) == 1

    # From host h1 (same host), dead PID is gone -> stale at +5s
    monkeypatch.setattr(socket, "gethostname", lambda: "h1")
    st_local = pool_mod.pool_status(real_home=real_home, now=t_1000_05)
    assert st_local["state"] == "ok"
    assert st_local["profiles"][0]["leased_by"] == []


def test_fpg_ar_06_concurrent_acquirers_never_share_a_profile(tmp_path: Path) -> None:
    """FPG-AR-06: Concurrent orchestrators never share a profile and never lose lease-file updates."""
    _pool_mod()
    real_home = tmp_path / "real_home"
    _make_profile_dirs(real_home, ("p1", "p2"))
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": "p1", "priority": 1},
                {"profile": "p2", "priority": 2},
            ],
            "lease_ttl_seconds": 180,
            "heartbeat_seconds": 30,
            "exhausted_recheck_seconds": 600,
            "agy_extra_args": [],
        },
    )

    worker_code = f"""
import importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("agy_profile_pool", {str(POOL_SCRIPT)!r})
mod = importlib.util.module_from_spec(spec)
sys.modules["agy_profile_pool"] = mod
spec.loader.exec_module(mod)
idx = sys.argv[1]
acq = mod.acquire(
    {{"repo": "r", "epic": "e", "task": f"t{{idx}}", "slot": int(idx), "role": "orchestrator"}},
    real_home=Path({str(real_home)!r}),
    host_profile="px",
    quota_pool="gemini5h",
    thresholds={{"5h_min_fraction": 0.15, "7d_min_fraction": 0.02, "agy_argon_min_fraction": 0.10}},
    fetcher=lambda _p: {{"status": "ACTIVE", "gemini5h": {{"fraction": 0.9}}, "geminiWeekly": {{"fraction": 0.9}}}},
    resident_probe=lambda _p: False,
    wait_seconds=0,
)
print(json.dumps({{"profile": acq.profile, "owner_id": acq.owner_id, "reason": acq.reason}}), flush=True)
sys.stdin.read()
"""
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", worker_code, str(i)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(6)
    ]

    results: list[dict[str, Any]] = []
    try:
        for p in procs:
            assert p.stdout is not None
            line = p.stdout.readline()
            assert line, (
                f"Worker exited without output; stderr={p.stderr.read() if p.stderr else ''}"
            )
            results.append(json.loads(line))

        acquired = [r for r in results if r["profile"] is not None]
        rejected = [r for r in results if r["profile"] is None]
        assert len(acquired) == 2
        assert sorted(r["profile"] for r in acquired) == ["p1", "p2"]
        assert all(r["reason"] == "pool_busy" for r in rejected)

        leases_doc = json.loads(
            (real_home / ".d3nexus" / "agy_profile_leases.json").read_text(
                encoding="utf-8"
            )
        )
        assert leases_doc["schema_version"] == 1
        all_leases = [
            lease
            for p_entry in leases_doc["profiles"].values()
            for lease in p_entry["leases"]
        ]
        assert len(all_leases) == 2
        assert len({lease["owner_id"] for lease in all_leases}) == 2
    finally:
        for p in procs:
            if p.stdin:
                p.stdin.close()
        for p in procs:
            p.wait(timeout=10)


def test_fpg_fr_07_exhausted_pool_report_and_recovery(tmp_path: Path) -> None:
    """FPG-FR-07: Exhausted pool yields exact report lines, top-up recovers after recheck, clear resets state."""
    pool_mod = _pool_mod()
    persona_mod = _persona_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    project.mkdir()
    _make_profile_dirs(real_home, ("p1", "p2"))
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": "p1", "priority": 1},
                {"profile": "p2", "priority": 2},
            ],
            "lease_ttl_seconds": 180,
            "heartbeat_seconds": 30,
            "exhausted_recheck_seconds": 600,
            "agy_extra_args": [],
        },
    )

    catalogue = {
        "hydrogen": {
            "cli": "agy",
            "id": "gemini-4-hydrogen-{effort}",
            "efforts": ["high", "xhigh"],
        },
        "codex-gpt": {
            "cli": "codex",
            "id": "gpt-6.1-sol",
            "efforts": ["medium", "high", "xhigh"],
        },
        "kiro-opus": {"cli": "kiro", "id": "claude-opus-5.5", "efforts": ["high"]},
    }
    prog_binding = persona_mod.PersonaBinding(
        persona="programmer",
        alias="hydrogen",
        cli="agy",
        model_id="gemini-4-hydrogen-xhigh",
        effort="xhigh",
        quota_pool="gemini5h",
        fallback_alias="codex-gpt",
        sources={"model": "kit", "effort": "kit", "fallback_model": "kit"},
    )
    thresholds = {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "agy_argon_min_fraction": 0.10,
    }

    p1_quota = {
        "status": "ACTIVE",
        "gemini5h": {"fraction": 0.02, "resetTime": "2026-11-17T11:43:00Z"},
        "geminiWeekly": {"fraction": 0.50, "resetTime": "2026-11-22T00:00:00Z"},
    }
    p2_quota = {
        "status": "ACTIVE",
        "gemini5h": {"fraction": 0.60, "resetTime": "2026-11-17T12:00:00Z"},
        "geminiWeekly": {"fraction": 0.01, "resetTime": "2026-11-21T00:54:00Z"},
    }

    t_1000 = datetime(2026, 11, 17, 10, 0, 0, tzinfo=timezone.utc)
    acq1 = pool_mod.acquire(
        {"epic": "e1", "task": "t1", "slot": 1, "role": "orchestrator"},
        real_home=real_home,
        host_profile="px",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=lambda p: p1_quota if p == "p1" else p2_quota,
        resident_probe=lambda _p: False,
        wait_seconds=0,
        now=t_1000,
    )
    assert acq1.profile is None
    assert acq1.reason == "pool_exhausted"

    leases_doc = json.loads(
        (real_home / ".d3nexus" / "agy_profile_leases.json").read_text(encoding="utf-8")
    )
    assert leases_doc["profiles"]["p1"]["exhausted_reason"] == "5h"
    assert leases_doc["profiles"]["p1"]["exhausted_until"] == "2026-11-17T11:43:00Z"
    assert leases_doc["profiles"]["p2"]["exhausted_reason"] == "weekly"
    assert leases_doc["profiles"]["p2"]["exhausted_until"] == "2026-11-21T00:54:00Z"

    status = pool_mod.pool_status(real_home=real_home, now=t_1000)
    assert status["state"] == "exhausted"
    report = pool_mod.exhaustion_report(
        status,
        catalogue=catalogue,
        programmer_binding=prog_binding,
        which=lambda cli: "/usr/bin/codex" if cli == "codex" else None,
    )
    assert report[0] == "Stopped: all agy profiles are out of quota."
    assert "- p1: 5-hour limit reached (resets 2026-11-17T11:43:00Z)" in report
    assert "- p2: weekly limit reached (resets 2026-11-21T00:54:00Z)" in report
    assert "Earliest reset: 2026-11-17T11:43:00Z." in report
    assert any(
        "wait for the reset or top up the quota" in line
        and "/d3nexus:dev-config profiles clear" in line
        for line in report
    )
    assert any(
        line
        == "- switch the programmer: /d3nexus:dev-config set programmer codex-gpt xhigh"
        for line in report
    )
    kiro_lines = [
        line
        for line in report
        if "/d3nexus:dev-config set programmer kiro-opus high" in line
    ]
    assert len(kiro_lines) == 1
    assert '"kiro" CLI not on PATH' in kiro_lines[0]

    # Top-up: at 10:11 UTC (>600s after 10:00), p1 is re-probed and acquired
    t_1011 = datetime(2026, 11, 17, 10, 11, 0, tzinfo=timezone.utc)
    p1_topped_up = {
        "status": "ACTIVE",
        "gemini5h": {"fraction": 0.60, "resetTime": "2026-11-17T15:00:00Z"},
        "geminiWeekly": {"fraction": 0.50, "resetTime": "2026-11-22T00:00:00Z"},
    }
    acq2 = pool_mod.acquire(
        {"epic": "e1", "task": "t1", "slot": 1, "role": "orchestrator"},
        real_home=real_home,
        host_profile="px",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=lambda p: p1_topped_up if p == "p1" else p2_quota,
        resident_probe=lambda _p: False,
        wait_seconds=0,
        now=t_1011,
    )
    assert acq2.profile == "p1"
    pool_mod.release(acq2.owner_id, real_home=real_home, now=t_1011)

    # Mark p2 exhausted again and clear via CLI
    pool_mod.mark_exhausted(
        "p2", "2026-11-21T00:54:00Z", reason="weekly", real_home=real_home, now=t_1011
    )
    env = _subproc_env(real_home)
    clear_proc = subprocess.run(
        [
            sys.executable,
            str(DEV_CONFIG_SCRIPT),
            "--project-root",
            str(project),
            "profiles",
            "clear",
            "p2",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert clear_proc.returncode == 0
    leases_after = json.loads(
        (real_home / ".d3nexus" / "agy_profile_leases.json").read_text(encoding="utf-8")
    )
    assert leases_after["profiles"]["p2"]["exhausted_until"] is None
    assert leases_after["profiles"]["p2"]["exhausted_reason"] is None
    assert leases_after["profiles"]["p2"]["quota"] is None


def test_fpg_hp_11_quota_check_judges_weekly_and_dry_run_pool(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """FPG-HP-11: quota-check enforces weekly Gemini window without pool and dry-runs acquire with pool."""
    pool_mod = _pool_mod()
    dev_config_mod = _dev_config_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    _make_profile_dirs(real_home, ("p1", "p2"))
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {"overrides": {"programmer": {"model": "hydrogen", "effort": "xhigh"}}},
    )

    # No pool: weekly threshold failure triggers exit 2 and formats 5H=... 7D=...
    rc = dev_config_mod.cmd_quota_check(
        project,
        personas=("programmer",),
        json_output=True,
        fetcher=lambda _cli: {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.80},
            "geminiWeekly": {"fraction": 0.02},
        },
        real_home=real_home,
    )
    assert rc == 2
    out = json.loads(capsys.readouterr().out)
    assert out["personas"][0]["sufficient"] is False
    assert out["personas"][0]["quota_line"] == "5H=80.0% 7D=2.0%"

    # With pool configured: dry-run acquire picks p2 (p1 low weekly), claims NO lease, names p2 in quota_line
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": "p1", "priority": 1},
                {"profile": "p2", "priority": 2},
            ],
        },
    )

    def pool_fetcher(name: str) -> dict[str, Any]:
        if name == "p1":
            return {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.80},
                "geminiWeekly": {"fraction": 0.01},
            }
        return {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.80},
            "geminiWeekly": {"fraction": 0.50},
        }

    rc_pool = dev_config_mod.cmd_quota_check(
        project,
        personas=("programmer",),
        json_output=True,
        fetcher=pool_fetcher,
        real_home=real_home,
        resident_probe=lambda _p: False,
    )
    assert rc_pool == 0
    out_pool = json.loads(capsys.readouterr().out)
    assert out_pool["personas"][0]["sufficient"] is True
    assert "p2" in out_pool["personas"][0]["quota_line"]

    # Dry run must not have claimed any lease
    st = pool_mod.pool_status(real_home=real_home)
    assert all(entry["leased_by"] == [] for entry in st["profiles"])


def test_fpg_st_07_busy_report_cache_and_host_detection(tmp_path: Path) -> None:
    """FPG-ST-07: Host profile detection, 120s quota cache reuse, busy report format, and release/probe CLI."""
    pool_mod = _pool_mod()
    persona_mod = _persona_mod()
    dev_config_mod = _dev_config_mod()

    assert (
        pool_mod.detect_host_profile({"AGY_PROFILE": "hau", "HOME": "/Users/x"})
        == "hau"
    )
    assert (
        pool_mod.detect_host_profile({"HOME": "/Users/x/antigravity_homes/tess"})
        == "tess"
    )
    assert pool_mod.detect_host_profile({"HOME": "/Users/x"}) is None

    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    project.mkdir()
    _make_profile_dirs(real_home, ("p1",))
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {"schema_version": 1, "pool": [{"profile": "p1", "priority": 1}]},
    )

    fetch_count = 0
    # `cmd_profiles_release` has no clock argument and reads the real clock, so every
    # fixture timestamp in this test is an offset from one real "now".
    t0 = datetime.now(timezone.utc).replace(microsecond=0)

    def counting_fetcher(_p: str) -> dict[str, Any]:
        nonlocal fetch_count
        fetch_count += 1
        return {
            "status": "ACTIVE",
            "email": "secret@example.invalid",
            "gemini5h": {
                "fraction": 0.85,
                "resetTime": _iso_utc(t0 + timedelta(hours=4)),
            },
            "geminiWeekly": {
                "fraction": 0.65,
                "resetTime": _iso_utc(t0 + timedelta(days=5)),
            },
        }

    thresholds = {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "agy_argon_min_fraction": 0.10,
    }
    a1 = pool_mod.acquire(
        {"epic": "e1", "task": "t1", "slot": 2, "role": "orchestrator"},
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=counting_fetcher,
        resident_probe=lambda _p: False,
        now=t0,
    )
    assert a1.profile == "p1"
    assert fetch_count == 1

    # Busy report check while a1 holds p1 (before marking exhausted)
    st_busy = pool_mod.pool_status(real_home=real_home, now=t0)
    assert st_busy["state"] == "busy"
    prog_binding = persona_mod.resolve_persona(
        "programmer", project, real_home=real_home
    )
    busy_report = pool_mod.exhaustion_report(
        st_busy,
        catalogue={},
        programmer_binding=prog_binding,
        wait_seconds=15,
    )
    assert busy_report == [
        "Stopped: every agy profile stayed in use for 15 seconds.",
        "- p1 is held by e1/t1/slot 2",
    ]

    # mark_exhausted must not touch leases
    pool_mod.mark_exhausted(
        "p1",
        _iso_utc(t0 + timedelta(hours=2)),
        reason="5h",
        real_home=real_home,
        now=t0,
    )
    st_after_mark = pool_mod.pool_status(real_home=real_home, now=t0)
    assert len(st_after_mark["profiles"][0]["leased_by"]) == 1

    # release without --force fails naming owner; release --force succeeds
    with pytest.raises(pool_mod.AgyPoolError) as rel_exc:
        dev_config_mod.cmd_profiles_release(
            project, name="p1", force=False, real_home=real_home
        )
    assert a1.owner_id in str(rel_exc.value) or "e1/t1/slot 2" in str(rel_exc.value)
    assert (
        dev_config_mod.cmd_profiles_release(
            project, name="p1", force=True, real_home=real_home
        )
        == 0
    )

    # Clear exhaustion before 120s cache check (simulate non-exhausted cached state: reset exhausted_until)
    # First re-acquire after clearing to populate fresh cache, then release and re-acquire within 120s
    pool_mod.clear_exhausted("p1", real_home=real_home)
    a2 = pool_mod.acquire(
        {"epic": "e1", "task": "t2", "slot": 1, "role": "orchestrator"},
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=counting_fetcher,
        resident_probe=lambda _p: False,
        now=t0,
    )
    assert a2.profile == "p1"
    assert fetch_count == 2
    pool_mod.release(a2.owner_id, real_home=real_home, now=t0)

    t_60 = t0 + timedelta(seconds=60)
    a3 = pool_mod.acquire(
        {"epic": "e1", "task": "t3", "slot": 1, "role": "orchestrator"},
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=counting_fetcher,
        resident_probe=lambda _p: False,
        now=t_60,
    )
    assert a3.profile == "p1"
    assert fetch_count == 2
    pool_mod.release(a3.owner_id, real_home=real_home, now=t_60)

    # Probe refreshes cache and stores no email
    assert (
        dev_config_mod.cmd_profiles_probe(
            project, name="p1", fetcher=counting_fetcher, real_home=real_home
        )
        == 0
    )
    assert fetch_count == 3
    leases_text = (real_home / ".d3nexus" / "agy_profile_leases.json").read_text(
        encoding="utf-8"
    )
    assert "@example.invalid" not in leases_text


def test_fpg_hp_17_profiles_discover_lists_candidates_not_in_the_pool(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """FPG-HP-17: profiles discover lists the profiles that could be added and fetches no quota."""
    pool_mod = _pool_mod()
    dc_mod = _dev_config_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    project.mkdir()
    _make_profile_dirs(real_home, ("profile_b",))
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [{"profile": "profile_b", "priority": 1}],
            "lease_ttl_seconds": 180,
            "heartbeat_seconds": 30,
            "exhausted_recheck_seconds": 600,
            "agy_extra_args": [],
        },
    )
    pool_path = real_home / ".d3nexus" / "agy_profiles.json"
    lease_path = real_home / ".d3nexus" / "agy_profile_leases.json"
    pool_before = pool_path.read_bytes()

    fetched: list[str] = []

    def recording_fetcher(profile: str) -> dict[str, Any]:
        fetched.append(profile)
        return {}

    monkeypatch.setattr(pool_mod, "default_fetcher", recording_fetcher)
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("REAL_HOME", str(real_home))
    monkeypatch.setenv("AGY_PROFILE", "profile_c")
    monkeypatch.setattr(
        dc_mod,
        "_discover_agy_profiles",
        lambda: ["profile_d", "profile_b", "profile_c", "profile_a"],
    )

    rc = dc_mod.main(["--project-root", str(project), "profiles", "discover", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["candidates"] == [
        {"profile": "profile_a", "host": False},
        {"profile": "profile_c", "host": True},
        {"profile": "profile_d", "host": False},
    ]
    assert payload["in_pool"] == ["profile_b"]
    assert payload["source"] == "agy_quota.get_all_profiles"

    rc_text = dc_mod.main(["--project-root", str(project), "profiles", "discover"])
    assert rc_text == 0
    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    candidate_lines = [
        line for line in lines if "profile_" in line and "profiles " not in line
    ]
    assert [line.split()[0] for line in candidate_lines] == [
        "profile_a",
        "profile_c",
        "profile_d",
    ]
    assert "profile_b" not in "\n".join(candidate_lines)
    text = "\n".join(lines)
    assert "profiles probe <name>" in text
    assert "profiles add <name>" in text

    assert fetched == []
    assert pool_path.read_bytes() == pool_before
    assert not lease_path.exists()


def _setup_isolated_probe_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    pool_names: tuple[str, ...] = ("profile_b",),
    create_pool_file: bool = True,
) -> tuple[Path, Path, Path, Path]:
    real_home = tmp_path / "real_home"
    real_home.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    if pool_names:
        _make_profile_dirs(real_home, pool_names)
    pool_path = real_home / ".d3nexus" / "agy_profiles.json"
    if create_pool_file:
        _write_json(
            pool_path,
            {
                "schema_version": 1,
                "pool": [
                    {"profile": name, "priority": idx + 1}
                    for idx, name in enumerate(pool_names)
                ],
                "lease_ttl_seconds": 180,
                "heartbeat_seconds": 30,
                "exhausted_recheck_seconds": 600,
                "agy_extra_args": [],
            },
        )
    lease_path = real_home / ".d3nexus" / "agy_profile_leases.json"
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("REAL_HOME", str(real_home))
    monkeypatch.delenv("AGY_PROFILE", raising=False)
    monkeypatch.delenv("ANTIGRAVITY_PROFILE", raising=False)
    return real_home, project, pool_path, lease_path


@pytest.mark.parametrize("create_pool_file", [True, False])
def test_se_16_profiles_probe_usable_non_pool_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    create_pool_file: bool,
) -> None:
    """SE-16: profiles probe tests a usable non-pool discoverable profile without writing pool or lease files."""
    pool_mod = _pool_mod()
    dc_mod = _dev_config_mod()
    pool_names = ("profile_b",) if create_pool_file else ()
    real_home, project, pool_path, lease_path = _setup_isolated_probe_env(
        tmp_path,
        monkeypatch,
        pool_names=pool_names,
        create_pool_file=create_pool_file,
    )
    pool_before = pool_path.read_bytes() if pool_path.exists() else None

    fetched: list[str] = []
    probed_resident: list[str] = []

    def recording_fetcher(profile: str) -> dict[str, Any]:
        fetched.append(profile)
        return {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.85},
            "geminiWeekly": {"fraction": 0.65},
        }

    def recording_resident_probe(profile: str) -> bool:
        probed_resident.append(profile)
        return False

    monkeypatch.setattr(pool_mod, "default_fetcher", recording_fetcher)
    monkeypatch.setattr(pool_mod, "default_resident_probe", recording_resident_probe)
    monkeypatch.setattr(
        dc_mod,
        "_discover_agy_profiles",
        lambda: ["profile_d", "profile_b", "profile_c", "profile_a"],
    )

    rc = dc_mod.main(["--project-root", str(project), "profiles", "probe", "profile_a"])
    out = capsys.readouterr().out
    assert rc == 0
    assert fetched == ["profile_a"]
    assert probed_resident == ["profile_a"]
    assert "not in the pool" in out.lower()
    assert "5H=85.0%" in out
    assert "7D=65.0%" in out
    assert "usable" in out.lower()
    assert "not usable" not in out.lower()
    assert "resident" in out.lower()
    assert "/d3nexus:dev-config profiles add profile_a" in out
    if pool_before is not None:
        assert pool_path.read_bytes() == pool_before
    else:
        assert not pool_path.exists()
        assert not (pool_path.parent).exists()
    assert not lease_path.exists()

    direct_probed = pool_mod.probe_profiles(
        "profile_a",
        fetcher=recording_fetcher,
        discoverer=lambda: ["profile_b", "profile_a"],
        real_home=real_home,
    )
    assert direct_probed["profile_a"]["status"] == "ACTIVE"
    assert fetched == ["profile_a", "profile_a"]
    assert not lease_path.exists()


@pytest.mark.parametrize(
    ("case_name", "payload", "is_resident", "expected_fragments"),
    [
        (
            "below_5h_floor",
            {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.10},
                "geminiWeekly": {"fraction": 0.65},
            },
            False,
            ("5H=10.0%", "7D=65.0%", "not usable"),
        ),
        (
            "at_weekly_floor",
            {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.85},
                "geminiWeekly": {"fraction": 0.02},
            },
            False,
            ("5H=85.0%", "7D=2.0%", "not usable"),
        ),
        (
            "below_weekly_floor",
            {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.85},
                "geminiWeekly": {"fraction": 0.01},
            },
            False,
            ("5H=85.0%", "7D=1.0%", "not usable"),
        ),
        (
            "resident_process",
            {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.85},
                "geminiWeekly": {"fraction": 0.65},
            },
            True,
            ("5H=85.0%", "7D=65.0%", "not usable", "resident", "yes"),
        ),
        (
            "inactive_status",
            {
                "status": "DISABLED",
                "gemini5h": {"fraction": 0.85},
                "geminiWeekly": {"fraction": 0.65},
            },
            False,
            ("5H=85.0%", "7D=65.0%", "not usable"),
        ),
        (
            "empty_payload",
            {},
            False,
            ("5H=unknown", "7D=unknown", "not usable"),
        ),
        (
            "error_payload",
            {"error": "timeout"},
            False,
            ("5H=unknown", "7D=unknown", "not usable"),
        ),
    ],
)
def test_se_16_profiles_probe_unusable_non_pool_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case_name: str,
    payload: dict[str, Any],
    is_resident: bool,
    expected_fragments: tuple[str, ...],
) -> None:
    """SE-16: unusable non-pool profiles report verdict without suggesting profiles add."""
    _ = case_name
    pool_mod = _pool_mod()
    dc_mod = _dev_config_mod()
    real_home, project, pool_path, lease_path = _setup_isolated_probe_env(
        tmp_path, monkeypatch
    )
    pool_before = pool_path.read_bytes()

    fetched: list[str] = []

    def recording_fetcher(profile: str) -> dict[str, Any]:
        fetched.append(profile)
        return dict(payload)

    monkeypatch.setattr(pool_mod, "default_fetcher", recording_fetcher)
    monkeypatch.setattr(pool_mod, "default_resident_probe", lambda _p: is_resident)
    monkeypatch.setattr(
        dc_mod,
        "_discover_agy_profiles",
        lambda: ["profile_d", "profile_b", "profile_a"],
    )

    rc = dc_mod.main(["--project-root", str(project), "profiles", "probe", "profile_a"])
    out = capsys.readouterr().out
    assert rc == 0
    assert fetched == ["profile_a"]
    assert "not in the pool" in out.lower()
    for fragment in expected_fragments:
        assert fragment.lower() in out.lower()
    assert "profiles add" not in out
    assert pool_path.read_bytes() == pool_before
    assert not lease_path.exists()


def test_se_16_profiles_probe_unknown_name_errors_naming_both_lists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SE-16: probing an unknown profile exits 1 and names both pool and discovered lists."""
    pool_mod = _pool_mod()
    dc_mod = _dev_config_mod()
    real_home, project, pool_path, lease_path = _setup_isolated_probe_env(
        tmp_path, monkeypatch
    )
    pool_before = pool_path.read_bytes()

    fetched: list[str] = []
    monkeypatch.setattr(pool_mod, "default_fetcher", lambda p: fetched.append(p) or {})
    monkeypatch.setattr(
        dc_mod,
        "_discover_agy_profiles",
        lambda: ["profile_b", "profile_a", "profile_c"],
    )

    rc = dc_mod.main(["--project-root", str(project), "profiles", "probe", "mystery"])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    err = captured.err
    assert "Error:" in err
    assert "pool" in err.lower()
    assert "discovered" in err.lower()
    assert "profile_b" in err
    assert "profile_a" in err
    assert "profile_c" in err
    assert fetched == []
    assert pool_path.read_bytes() == pool_before
    assert not lease_path.exists()

    with pytest.raises(pool_mod.AgyPoolError) as exc_info:
        pool_mod.probe_profiles(
            "mystery",
            discoverer=lambda: ["profile_b", "profile_a"],
            real_home=real_home,
        )
    msg = str(exc_info.value)
    assert "profile_b" in msg
    assert "profile_a" in msg


@pytest.mark.parametrize("target", ["p1", None])
def test_se_16_profiles_probe_pool_profile_and_no_name_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    target: str | None,
) -> None:
    """SE-16: probing a pool profile or all pool profiles still refreshes quota cache without calling discoverer."""
    pool_mod = _pool_mod()
    dc_mod = _dev_config_mod()
    _real_home, project, _pool_path, lease_path = _setup_isolated_probe_env(
        tmp_path, monkeypatch, pool_names=("p1", "p2")
    )

    fetched: list[str] = []

    def recording_fetcher(profile: str) -> dict[str, Any]:
        fetched.append(profile)
        return {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.90},
            "geminiWeekly": {"fraction": 0.70},
        }

    def fail_if_discovered() -> list[str]:
        raise AssertionError("discoverer must not be called for pool probe")

    monkeypatch.setattr(pool_mod, "default_fetcher", recording_fetcher)
    monkeypatch.setattr(dc_mod, "_discover_agy_profiles", fail_if_discovered)

    argv = ["--project-root", str(project), "profiles", "probe"]
    if target is not None:
        argv.append(target)
    rc = dc_mod.main(argv)
    out = capsys.readouterr().out
    assert rc == 0
    expected = ["p1"] if target == "p1" else ["p1", "p2"]
    assert fetched == expected
    for name in expected:
        assert f"Probed '{name}': status=ACTIVE" in out
    assert lease_path.is_file()
    leases_doc = json.loads(lease_path.read_text(encoding="utf-8"))
    for name in expected:
        assert leases_doc["profiles"][name]["quota"]["status"] == "ACTIVE"


@pytest.mark.parametrize("seconds_past_reset", [0, 30])
def test_quota_cache_bypassed_once_exhausted_until_passes(
    tmp_path: Path, seconds_past_reset: int
) -> None:
    """S4: The 120s quota cache must be bypassed once exhausted_until <= now."""
    pool_mod = _pool_mod()
    real_home = tmp_path / "real_home"
    _make_profile_dirs(real_home, ("p1",))
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [{"profile": "p1", "priority": 1}],
            "exhausted_recheck_seconds": 600,
        },
    )
    thresholds = {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "agy_argon_min_fraction": 0.10,
    }
    t0 = datetime(2026, 11, 17, 10, 0, 0, tzinfo=timezone.utc)
    reset_at = t0 + timedelta(seconds=60)
    t_before = t0 + timedelta(seconds=30)
    t_after = reset_at + timedelta(seconds=seconds_past_reset)
    t_cached = t_after + timedelta(seconds=30)

    clock = t0
    fetch_times: list[datetime] = []

    def fake_fetcher(_profile: str) -> dict[str, Any]:
        fetch_times.append(clock)
        if clock < reset_at:
            return {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.02, "resetTime": _iso_utc(reset_at)},
                "geminiWeekly": {"fraction": 0.80, "resetTime": "2026-11-22T00:00:00Z"},
            }
        return {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.90, "resetTime": "2026-11-17T15:00:00Z"},
            "geminiWeekly": {"fraction": 0.80, "resetTime": "2026-11-22T00:00:00Z"},
        }

    owner = {"epic": "e1", "task": "t1", "slot": 1, "role": "orchestrator"}
    acq_exhausted = pool_mod.acquire(
        owner,
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=fake_fetcher,
        resident_probe=lambda _p: False,
        now=clock,
    )
    assert acq_exhausted.profile is None
    assert acq_exhausted.reason == "pool_exhausted"
    assert len(fetch_times) == 1

    clock = t_before
    acq_still_exhausted = pool_mod.acquire(
        owner,
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=fake_fetcher,
        resident_probe=lambda _p: False,
        now=clock,
    )
    assert acq_still_exhausted.profile is None
    assert acq_still_exhausted.skipped == {"p1": "exhausted"}
    assert len(fetch_times) == 1

    # Still within 120s of t0, but exhausted_until <= now: cache must be bypassed
    clock = t_after
    acq_recovered = pool_mod.acquire(
        owner,
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=fake_fetcher,
        resident_probe=lambda _p: False,
        now=clock,
    )
    assert acq_recovered.profile == "p1"
    assert len(fetch_times) == 2
    pool_mod.release(acq_recovered.owner_id, real_home=real_home, now=clock)

    # After recovery cleared exhausted_until, subsequent acquires within 120s reuse fresh cache
    clock = t_cached
    acq_cached = pool_mod.acquire(
        owner,
        real_home=real_home,
        host_profile="other",
        quota_pool="gemini5h",
        thresholds=thresholds,
        fetcher=fake_fetcher,
        resident_probe=lambda _p: False,
        now=clock,
    )
    assert acq_cached.profile == "p1"
    assert len(fetch_times) == 2
    pool_mod.release(acq_cached.owner_id, real_home=real_home, now=clock)


@pytest.mark.parametrize("payload", [{}, {"error": "timeout"}])
def test_quota_check_pool_empty_payload_propagates_quota_unknown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], payload: dict[str, Any]
) -> None:
    """S5: Pool quota-check must propagate quota_unknown even when the chosen payload is an empty dict."""
    dev_config_mod = _dev_config_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    _make_profile_dirs(real_home, ("p1",))
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {"overrides": {"programmer": {"model": "hydrogen", "effort": "xhigh"}}},
    )
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {"schema_version": 1, "pool": [{"profile": "p1", "priority": 1}]},
    )

    rc = dev_config_mod.cmd_quota_check(
        project,
        personas=("programmer",),
        json_output=True,
        fetcher=lambda _p: dict(payload),
        real_home=real_home,
        resident_probe=lambda _p: False,
    )
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["sufficient"] is True
    entry = out["personas"][0]
    assert entry["sufficient"] is True
    assert entry["quota_line"] == "profile=p1"
    assert entry["warning"] == "quota_unknown"
