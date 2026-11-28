"""Tests for dev-config set with a provider, a model, an effort and a preferred agy profile.

Covers BDD Scenarios:
- FPG-HP-14: dev-config set accepts a provider, a model, an effort and a preferred agy profile
- FPG-HP-15: A preferred agy profile is tried first and the pool rotates when it is unusable
- FPG-HP-17: profiles discover lists the profiles that could be added and fetches no quota (CLI wiring;
  the injected-discoverer unit test lives in tests/test_fpg_agy_profile_pool.py)
- FPG-EC-08: Invalid provider, model, effort and profile combinations are rejected and change nothing
- FPG-FR-08: The exhaustion report offers Kiro claude-sonnet-5.5 at high effort with the default catalogue
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONA_CONFIG_SCRIPT = REPO_ROOT / "scripts" / "persona_config.py"
DEV_CONFIG_SCRIPT = REPO_ROOT / "scripts" / "dev_config.py"
POOL_SCRIPT = REPO_ROOT / "scripts" / "agy_profile_pool.py"
DISPATCH_SCRIPT = REPO_ROOT / "scripts" / "agy_dispatch.py"


def _load_module(name: str, path: Path) -> ModuleType:
    """Load a module by path via importlib so the RED phase fails as a test failure."""
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


def _persona_mod() -> ModuleType:
    return _load_module("persona_config", PERSONA_CONFIG_SCRIPT)


def _pool_mod() -> ModuleType:
    return _load_module("agy_profile_pool", POOL_SCRIPT)


def _dispatch_mod() -> ModuleType:
    return _load_module("agy_dispatch", DISPATCH_SCRIPT)


@pytest.fixture(autouse=True)
def _isolated_host(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point HOME and REAL_HOME at a temporary directory and drop the profile variables."""
    host_home = tmp_path / "host_home"
    host_home.mkdir()
    monkeypatch.setenv("HOME", str(host_home))
    monkeypatch.setenv("REAL_HOME", str(host_home))
    monkeypatch.delenv("AGY_PROFILE", raising=False)
    monkeypatch.delenv("ANTIGRAVITY_PROFILE", raising=False)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_stub_bin(bin_dir: Path, names: tuple[str, ...]) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        exe = bin_dir / name
        exe.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        exe.chmod(0o755)


def _make_pool(
    real_home: Path, names: tuple[str, ...], *, max_concurrent: int = 2
) -> None:
    homes = real_home / "antigravity_homes"
    for name in names:
        (homes / name).mkdir(parents=True, exist_ok=True)
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": name, "priority": idx + 1, "max_concurrent": max_concurrent}
                for idx, name in enumerate(names)
            ],
            "lease_ttl_seconds": 180,
            "heartbeat_seconds": 30,
            "exhausted_recheck_seconds": 600,
            "agy_extra_args": [],
        },
    )


def _run_cli(
    args: list[str],
    *,
    cwd: Path,
    real_home: Path,
    path_dir: Path,
) -> subprocess.CompletedProcess[str]:
    if not DEV_CONFIG_SCRIPT.is_file():
        pytest.fail(f"Expected CLI script does not exist yet: {DEV_CONFIG_SCRIPT}")
    env = dict(os.environ)
    env["HOME"] = str(real_home)
    env["REAL_HOME"] = str(real_home)
    for key in ("AGY_PROFILE", "ANTIGRAVITY_PROFILE"):
        env.pop(key, None)
    env["PATH"] = str(path_dir)
    return subprocess.run(
        [sys.executable, str(DEV_CONFIG_SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _resolve(project: Path, real_home: Path, bin_dir: Path) -> dict[str, Any]:
    res = _run_cli(
        ["resolve", "programmer", "--format", "json"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res.returncode == 0, res.stderr
    payload: dict[str, Any] = json.loads(res.stdout)
    return payload


def _init_git_repo(repo_dir: Path) -> None:
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repo_dir,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True
    )
    (repo_dir / "README.md").write_text("init\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo_dir, check=True)


def _healthy_fetcher(_profile: str) -> dict[str, Any]:
    return {
        "status": "ACTIVE",
        "gemini5h": {"fraction": 0.90, "resetTime": "2026-11-17T14:00:00Z"},
        "geminiWeekly": {"fraction": 0.80, "resetTime": "2026-11-22T00:00:00Z"},
        "argonWeekly": {"fraction": 0.80, "resetTime": "2026-11-22T00:00:00Z"},
    }


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_record() -> dict[str, Any]:
    return {
        "leases": [],
        "exhausted_until": None,
        "exhausted_checked_at": None,
        "exhausted_reason": None,
        "quota": None,
    }


class Test_Integration:
    """[Tier C - Integration] Subprocess CLI integration tests for dev_config.py set."""

    def test_fpg_hp_14_set_flags_end_to_end_with_stub_clis(
        self, tmp_path: Path
    ) -> None:
        """FPG-HP-14: Tier C subprocess run of set with flags, positional form and the catalogue."""
        real_home = tmp_path / "real_home"
        project = tmp_path / "project"
        bin_dir = tmp_path / "bin"
        real_home.mkdir()
        project.mkdir()
        _make_stub_bin(bin_dir, ("agy", "claude", "codex", "kiro-cli"))
        _make_pool(real_home, ("p1", "p2"))

        res_kiro = _run_cli(
            [
                "set",
                "programmer",
                "--provider",
                "kiro",
                "--model",
                "claude-sonnet-5.5",
                "--effort",
                "high",
            ],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_kiro.returncode == 0, res_kiro.stderr
        resolved = _resolve(project, real_home, bin_dir)
        assert resolved["cli"] == "kiro"
        assert resolved["alias"] == "kiro-sonnet"
        assert resolved["model_id"] == "claude-sonnet-5.5"
        assert resolved["effort"] == "high"
        assert resolved["profile"] is None

        res_agy = _run_cli(
            [
                "set",
                "programmer",
                "--provider",
                "agy",
                "--model",
                "hydrogen",
                "--effort",
                "xhigh",
            ],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_agy.returncode == 0, res_agy.stderr
        resolved = _resolve(project, real_home, bin_dir)
        assert resolved["cli"] == "agy"
        assert resolved["model_id"] == "gemini-4-hydrogen-xhigh"
        assert resolved["effort"] == "xhigh"
        assert resolved["profile"] is None
        assert "profile" not in resolved["sources"]

        res_status = _run_cli(
            ["status", "--json"], cwd=project, real_home=real_home, path_dir=bin_dir
        )
        assert res_status.returncode == 0, res_status.stderr
        assert (
            json.loads(res_status.stdout)["personas"]["programmer"]["profile"] is None
        )

        res_positional = _run_cli(
            ["set", "programmer", "codex-gpt", "xhigh"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_positional.returncode == 0, res_positional.stderr
        resolved = _resolve(project, real_home, bin_dir)
        assert resolved["cli"] == "codex"
        assert resolved["profile"] is None
        global_cfg = json.loads(
            (real_home / ".d3nexus" / "personas.json").read_text(encoding="utf-8")
        )
        assert global_cfg["overrides"]["programmer"] == {
            "model": "codex-gpt",
            "effort": "xhigh",
        }

        res_agy_pos = _run_cli(
            ["set", "programmer", "hydrogen", "xhigh"],
            cwd=project,
            real_home=real_home,
            path_dir=bin_dir,
        )
        assert res_agy_pos.returncode == 0, res_agy_pos.stderr
        assert _resolve(project, real_home, bin_dir)["profile"] is None

        res_models = _run_cli(
            ["models", "--json"], cwd=project, real_home=real_home, path_dir=bin_dir
        )
        assert res_models.returncode == 0, res_models.stderr
        entries = json.loads(res_models.stdout)["models"]
        aliases = [entry["alias"] for entry in entries]
        sonnet = entries[aliases.index("kiro-sonnet")]
        assert (sonnet["cli"], sonnet["id"], sonnet["efforts"]) == (
            "kiro",
            "claude-sonnet-5.5",
            ["high"],
        )
        assert aliases.index("kiro-sonnet") < aliases.index("kiro-opus")


def _dev_config_mod() -> ModuleType:
    return _load_module("dev_config", DEV_CONFIG_SCRIPT)


def test_fpg_hp_14_set_with_provider_model_effort_and_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FPG-HP-14: set accepts --provider, --model, and --effort in one call."""
    pc = _persona_mod()
    dc = _dev_config_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    project.mkdir()
    _make_pool(real_home, ("p1", "p2"))
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("REAL_HOME", str(real_home))

    def run(*args: str) -> int:
        return int(dc.main(["--project-root", str(project), *args]))

    assert (
        run(
            "set",
            "programmer",
            "--provider",
            "kiro",
            "--model",
            "claude-sonnet-5.5",
            "--effort",
            "high",
        )
        == 0
    )
    binding = pc.resolve_persona("programmer", project, real_home=real_home)
    assert (binding.cli, binding.alias, binding.model_id, binding.effort) == (
        "kiro",
        "kiro-sonnet",
        "claude-sonnet-5.5",
        "high",
    )
    assert binding.profile is None
    assert "profile" not in binding.sources

    assert (
        run(
            "set",
            "programmer",
            "--provider",
            "agy",
            "--model",
            "hydrogen",
            "--effort",
            "xhigh",
        )
        == 0
    )
    binding = pc.resolve_persona("programmer", project, real_home=real_home)
    assert (binding.cli, binding.model_id, binding.effort) == (
        "agy",
        "gemini-4-hydrogen-xhigh",
        "xhigh",
    )
    assert binding.profile is None
    assert "profile" not in binding.sources

    assert (
        run(
            "set",
            "programmer",
            "--model",
            "gemini-4-hydrogen-xhigh",
            "--effort",
            "xhigh",
        )
        == 0
    )
    binding = pc.resolve_persona("programmer", project, real_home=real_home)
    assert (binding.alias, binding.profile) == ("hydrogen", None)

    assert run("set", "programmer", "codex-gpt", "xhigh") == 0
    binding = pc.resolve_persona("programmer", project, real_home=real_home)
    assert (binding.cli, binding.profile) == ("codex", None)
    cfg = json.loads(
        (real_home / ".d3nexus" / "personas.json").read_text(encoding="utf-8")
    )
    assert cfg["overrides"]["programmer"] == {"model": "codex-gpt", "effort": "xhigh"}


def test_fpg_hp_17_profiles_discover_cli_lists_candidates_from_a_temporary_home(
    tmp_path: Path,
) -> None:
    """FPG-HP-17: the CLI wiring of profiles discover reads only the temporary home and writes nothing."""
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    real_home.mkdir()
    project.mkdir()
    _make_stub_bin(bin_dir, ("agy",))
    _make_pool(real_home, ("p1",))
    for name in ("p1", "cand1"):
        (real_home / "antigravity_homes" / name / ".gemini").mkdir(
            parents=True, exist_ok=True
        )
    pool_path = real_home / ".d3nexus" / "agy_profiles.json"
    pool_before = pool_path.read_bytes()

    res = _run_cli(
        ["profiles", "discover", "--json"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    assert payload["candidates"] == [{"profile": "cand1", "host": False}]
    assert payload["in_pool"] == ["p1"]
    assert payload["source"] == "agy_quota.get_all_profiles"

    text = _run_cli(
        ["profiles", "discover"], cwd=project, real_home=real_home, path_dir=bin_dir
    )
    assert text.returncode == 0, text.stderr
    assert "cand1" in text.stdout
    assert "profiles probe <name>" in text.stdout
    assert "profiles add <name>" in text.stdout
    assert pool_path.read_bytes() == pool_before
    assert not (real_home / ".d3nexus" / "agy_profile_leases.json").exists()


def test_fpg_hp_15_priority_only_pool_rotation_ignores_legacy_persona_profile(
    tmp_path: Path,
) -> None:
    """FPG-HP-15: Pool acquisition and dispatch rotate strictly in priority order, ignoring legacy persona profile."""
    pc = _persona_mod()
    pool_mod = _pool_mod()
    dispatch_mod = _dispatch_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    repo = tmp_path / "repo"
    project.mkdir()
    _make_pool(real_home, ("p1", "p2", "p3"), max_concurrent=1)
    _write_json(
        real_home / ".d3nexus" / "personas.json",
        {
            "overrides": {
                "programmer": {"model": "hydrogen", "effort": "xhigh", "profile": "p3"}
            }
        },
    )
    binding = pc.resolve_persona("programmer", project, real_home=real_home)
    assert binding.cli == "agy"
    assert binding.profile is None
    assert "profile" not in binding.sources

    now = datetime(2026, 11, 17, 10, 0, 0, tzinfo=timezone.utc)
    thresholds = {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "agy_argon_min_fraction": 0.10,
    }
    owner = {"repo": "r", "epic": "e1", "task": "t1", "slot": 1, "role": "orchestrator"}
    leases_path = real_home / ".d3nexus" / "agy_profile_leases.json"

    def _acquire() -> Any:
        return pool_mod.acquire(
            owner,
            real_home=real_home,
            host_profile="px",
            quota_pool=binding.quota_pool,
            thresholds=thresholds,
            fetcher=_healthy_fetcher,
            resident_probe=lambda _p: False,
            wait_seconds=0,
            now=now,
        )

    first = _acquire()
    assert first.profile == "p1"
    assert first.skipped == {}
    pool_mod.release(first.owner_id, real_home=real_home, now=now)

    other_lease = {
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
    leased_record = _empty_record()
    leased_record["leases"] = [other_lease]
    _write_json(leases_path, {"schema_version": 1, "profiles": {"p1": leased_record}})
    leased = _acquire()
    assert leased.profile == "p2"
    assert leased.skipped == {"p1": "leased"}
    pool_mod.release(leased.owner_id, real_home=real_home, now=now)

    exhausted_record = _empty_record()
    exhausted_record["exhausted_until"] = _iso_utc(now + timedelta(hours=1))
    exhausted_record["exhausted_reason"] = "5h"
    _write_json(
        leases_path, {"schema_version": 1, "profiles": {"p1": exhausted_record}}
    )
    exhausted = _acquire()
    assert exhausted.profile == "p2"
    assert exhausted.skipped == {"p1": "exhausted"}
    pool_mod.release(exhausted.owner_id, real_home=real_home, now=now)

    _write_json(leases_path, {"schema_version": 1, "profiles": {}})
    _init_git_repo(repo)
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("implement feature\n", encoding="utf-8")
    calls: list[str | None] = []

    def launcher_all_quota(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        stdin_text: str,
        profile: str | None,
        via_ag_run: bool,
    ) -> tuple[int, str, str]:
        _ = (argv, cwd, env, stdin_text, via_ag_run)
        calls.append(profile)
        return (1, "", "RESOURCE_EXHAUSTED: quota exceeded")

    result = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=repo,
        log=tmp_path / "run.log",
        owner={"repo": "repo", "epic": "e1", "task": "t1", "slot": 1, "role": "runner"},
        real_home=real_home,
        host_profile="px",
        launcher=launcher_all_quota,
        fetcher=_healthy_fetcher,
        resident_probe=lambda _p: False,
        preflight=lambda: 0,
    )
    assert calls == ["p1", "p2", "p3"]
    assert result.status == "no_profile"


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (
            [
                "set",
                "programmer",
                "--provider",
                "kiro",
                "--model",
                "hydrogen",
                "--effort",
                "high",
            ],
            ["hydrogen", "not a kiro model"],
        ),
        (["set", "programmer", "--provider", "kiro", "--effort", "high"], ["--model"]),
        (
            [
                "set",
                "programmer",
                "--provider",
                "kiro",
                "--model",
                "claude-sonnet-5.5",
                "--effort",
                "xhigh",
            ],
            ["xhigh"],
        ),
        (
            ["set", "programmer", "--model", "no-such-model", "--effort", "high"],
            ["no-such-model", "models add"],
        ),
        (
            [
                "set",
                "programmer",
                "--provider",
                "codex",
                "--model",
                "codex-gpt",
                "--effort",
                "xhigh",
                "--profile",
                "p1",
            ],
            ["--profile"],
        ),
        (
            [
                "set",
                "programmer",
                "--provider",
                "agy",
                "--model",
                "hydrogen",
                "--effort",
                "xhigh",
                "--profile",
                "nope",
            ],
            ["--profile"],
        ),
        (
            ["set", "programmer", "codex-gpt", "xhigh", "--model", "codex-gpt"],
            ["positional"],
        ),
    ],
)
def test_fpg_ec_08_invalid_set_combinations_change_nothing(
    tmp_path: Path, args: list[str], expected: list[str]
) -> None:
    """FPG-EC-08: Invalid provider, model, effort and profile combinations are rejected and change nothing."""
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    real_home.mkdir()
    project.mkdir()
    _make_stub_bin(bin_dir, ("agy", "claude", "codex", "kiro-cli"))
    _make_pool(real_home, ("p1",))
    project_cfg = project / ".agents" / "config" / "personas.json"
    _write_json(
        project_cfg,
        {
            "schema_version": 1,
            "overrides": {"programmer": {"model": "codex-gpt", "effort": "xhigh"}},
        },
    )
    before = _sha256(project_cfg)

    res = _run_cli(
        [*args, "--scope", "project"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res.returncode == 1, (res.stdout, res.stderr)
    for fragment in expected:
        assert fragment in res.stderr, res.stderr
    assert _sha256(project_cfg) == before
    assert not (real_home / ".d3nexus" / "personas.json").exists()


def test_fpg_ec_08_provider_shortcut_still_rejects_a_subcommand(tmp_path: Path) -> None:
    """FPG-EC-08: the all-personas --provider shortcut cannot be combined with a subcommand."""
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    real_home.mkdir()
    project.mkdir()
    _make_stub_bin(bin_dir, ("agy", "claude"))
    res = _run_cli(
        ["--provider", "claude", "set", "programmer", "claude-sonnet", "high"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res.returncode == 1
    assert "set" in res.stderr
    assert not (real_home / ".d3nexus" / "personas.json").exists()


def test_fpg_fr_08_exhaustion_report_offers_kiro_sonnet(tmp_path: Path) -> None:
    """FPG-FR-08: The exhaustion report offers Kiro claude-sonnet-5.5 at high effort."""
    pc = _persona_mod()
    pool_mod = _pool_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    project.mkdir()
    _make_stub_bin(bin_dir, ("kiro-cli", "codex"))
    _make_pool(real_home, ("p1", "p2"))
    now = datetime(2026, 11, 17, 10, 0, 0, tzinfo=timezone.utc)
    records: dict[str, Any] = {}
    for name in ("p1", "p2"):
        record = _empty_record()
        record["exhausted_until"] = _iso_utc(now + timedelta(hours=2))
        record["exhausted_reason"] = "5h"
        records[name] = record
    _write_json(
        real_home / ".d3nexus" / "agy_profile_leases.json",
        {"schema_version": 1, "profiles": records},
    )

    binding = pc.resolve_persona("programmer", project, real_home=real_home)
    assert (binding.alias, binding.effort) == ("hydrogen", "xhigh")
    catalogue = pc.load_persona_config(project, real_home=real_home)["models"]
    status = pool_mod.pool_status(real_home=real_home, now=now)
    assert status["state"] == "exhausted"

    report = pool_mod.exhaustion_report(
        status,
        catalogue=catalogue,
        programmer_binding=binding,
        which=lambda name: shutil.which(name, path=str(bin_dir)),
    )
    assert (
        "- switch the programmer: /d3nexus:dev-config set programmer kiro-sonnet high"
        in report
    )
    assert (
        "- switch the programmer: /d3nexus:dev-config set programmer codex-gpt xhigh"
        in report
    )
    kiro_lines = [line for line in report if "set programmer kiro-sonnet" in line]
    assert len(kiro_lines) == 1
    assert "not on PATH" not in kiro_lines[0]
    joined = "\n".join(report)
    assert "kiro-opus" not in joined


@pytest.mark.parametrize(
    "exc",
    [
        TypeError("unsupported operand type(s) for |: 'type' and 'NoneType'"),
        SyntaxError("invalid syntax"),
    ],
)
def test_profiles_discover_reports_python_version_on_load_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    exc: Exception,
) -> None:
    """S6: profiles discover must report a one-line CLI error naming Python 3.10+ when loading agy_quota.py fails."""
    dc = _dev_config_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    project.mkdir()
    _make_pool(real_home, ("p1",))

    def failing_loader(_name: str, _path: Path) -> ModuleType:
        raise exc

    monkeypatch.setattr(dc, "_load_module_by_path", failing_loader)
    rc = dc.main(["--project-root", str(project), "profiles", "discover"])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    err_lines = [line for line in captured.err.splitlines() if line.strip()]
    assert len(err_lines) == 1
    assert err_lines[0].startswith("Error:")
    assert "3.10" in err_lines[0]

    with pytest.raises(dc.AgyPoolError) as err_info:
        dc._discover_agy_profiles(loader=failing_loader)
    assert "3.10" in str(err_info.value)
    assert "\n" not in str(err_info.value)


@pytest.mark.parametrize(
    "exc",
    [
        TypeError("unsupported operand type(s) for |: 'type' and 'NoneType'"),
        SyntaxError("invalid syntax"),
    ],
)
def test_profiles_probe_reports_python_version_on_load_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    exc: Exception,
) -> None:
    """SE-16: profiles probe reuses discover load-error handling when loading agy_quota.py fails."""
    dc = _dev_config_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    project.mkdir()
    _make_pool(real_home, ("p1",))

    def failing_loader(_name: str, _path: Path) -> ModuleType:
        raise exc

    monkeypatch.setattr(dc, "_load_module_by_path", failing_loader)
    rc = dc.main(["--project-root", str(project), "profiles", "probe", "cand1"])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    err_lines = [line for line in captured.err.splitlines() if line.strip()]
    assert len(err_lines) == 1
    assert err_lines[0].startswith("Error:")
    assert "3.10" in err_lines[0]


def test_se_16_profiles_probe_cli_unknown_name_and_help(tmp_path: Path) -> None:
    """SE-16: CLI wiring for profiles probe errors on unknown names naming both lists and documents outside-pool probe."""
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    real_home.mkdir()
    project.mkdir()
    _make_stub_bin(bin_dir, ("agy",))
    _make_pool(real_home, ("p1",))
    for name in ("p1", "cand1"):
        (real_home / "antigravity_homes" / name / ".gemini").mkdir(
            parents=True, exist_ok=True
        )
    pool_path = real_home / ".d3nexus" / "agy_profiles.json"
    pool_before = pool_path.read_bytes()

    err_res = _run_cli(
        ["profiles", "probe", "unknown_x"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert err_res.returncode == 1
    assert err_res.stdout == ""
    assert "p1" in err_res.stderr
    assert "cand1" in err_res.stderr
    assert "pool" in err_res.stderr.lower()
    assert "discovered" in err_res.stderr.lower()
    assert pool_path.read_bytes() == pool_before
    assert not (real_home / ".d3nexus" / "agy_profile_leases.json").exists()

    help_res = _run_cli(
        ["profiles", "probe", "--help"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert help_res.returncode == 0
    assert "discover" in help_res.stdout.lower()


_AGY_WITH_PROFILE = {"model": "hydrogen", "effort": "xhigh", "profile": "p1"}
_AGY_PLAIN = {"model": "hydrogen", "effort": "xhigh"}
_CODEX = {"model": "codex-gpt", "effort": "xhigh"}
_KIRO = {"model": "kiro-sonnet", "effort": "high"}


def _write_layers(
    real_home: Path,
    project: Path,
    *,
    global_override: dict[str, str] | None,
    project_override: dict[str, str] | None,
) -> None:
    """Write the programmer override of the global and project layers (None writes no entry)."""
    for path, override in (
        (real_home / ".d3nexus" / "personas.json", global_override),
        (project / ".agents" / "config" / "personas.json", project_override),
    ):
        if override is not None:
            _write_json(
                path, {"schema_version": 1, "overrides": {"programmer": override}}
            )


@pytest.mark.parametrize(
    (
        "global_override",
        "project_override",
        "cli_overrides",
        "expected_cli",
    ),
    [
        pytest.param(
            _AGY_WITH_PROFILE,
            _CODEX,
            None,
            "codex",
            id="global-profile-project-codex",
        ),
        pytest.param(
            _AGY_WITH_PROFILE,
            _KIRO,
            None,
            "kiro",
            id="global-profile-project-kiro",
        ),
        pytest.param(
            _AGY_WITH_PROFILE,
            None,
            _CODEX,
            "codex",
            id="global-profile-cli-codex",
        ),
        pytest.param(
            _AGY_WITH_PROFILE,
            _AGY_PLAIN,
            None,
            "agy",
            id="global-profile-project-agy-drops-profile",
        ),
        pytest.param(
            _AGY_WITH_PROFILE,
            None,
            {"model": "hydrogen", "effort": "xhigh"},
            "agy",
            id="global-profile-cli-agy-drops-profile",
        ),
        pytest.param(
            {**_CODEX, "profile": "p1"},
            None,
            None,
            "codex",
            id="same-layer-global-codex-profile-tolerated",
        ),
        pytest.param(
            None,
            {**_KIRO, "profile": "p1"},
            None,
            "kiro",
            id="same-layer-project-kiro-profile-tolerated",
        ),
        pytest.param(
            _CODEX,
            {"profile": "p1"},
            None,
            "codex",
            id="higher-layer-only-profile-with-lower-codex-tolerated",
        ),
    ],
)
def test_legacy_multilayer_profile_never_blocks_any_provider_resolution(
    tmp_path: Path,
    global_override: dict[str, str] | None,
    project_override: dict[str, str] | None,
    cli_overrides: dict[str, str] | None,
    expected_cli: str,
) -> None:
    """Legacy profile keys in global or project layers are ignored and never block agy/codex/kiro resolution."""
    pc = _persona_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    project.mkdir()
    _write_layers(
        real_home,
        project,
        global_override=global_override,
        project_override=project_override,
    )

    binding = pc.resolve_persona(
        "programmer", project, cli_overrides=cli_overrides, real_home=real_home
    )

    assert binding.cli == expected_cli
    assert binding.profile is None
    assert "profile" not in binding.sources


def test_retired_set_profile_rejected_and_set_prunes_legacy_profile(
    tmp_path: Path,
) -> None:
    """dev_config.py set --profile exits 1 without mutating personas.json, and valid set prunes legacy profile."""
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    real_home.mkdir()
    project.mkdir()
    _make_stub_bin(bin_dir, ("agy", "claude", "codex", "kiro-cli"))
    _make_pool(real_home, ("p1", "p2"))

    global_cfg_path = real_home / ".d3nexus" / "personas.json"
    _write_json(
        global_cfg_path,
        {
            "schema_version": 1,
            "overrides": {
                "programmer": {
                    "model": "hydrogen",
                    "effort": "high",
                    "profile": "p1",
                }
            },
        },
    )
    before = _sha256(global_cfg_path)

    for retired_args in (
        [
            "set",
            "programmer",
            "--provider",
            "agy",
            "--model",
            "hydrogen",
            "--effort",
            "xhigh",
            "--profile",
            "p1",
        ],
        ["set", "programmer", "hydrogen", "xhigh", "--profile", "p1"],
    ):
        res = _run_cli(retired_args, cwd=project, real_home=real_home, path_dir=bin_dir)
        assert res.returncode == 1, (retired_args, res.stdout, res.stderr)
        assert "--profile" in res.stderr
        assert _sha256(global_cfg_path) == before

    res_codex_proj = _run_cli(
        ["set", "programmer", "codex-gpt", "xhigh", "--scope", "project"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_codex_proj.returncode == 0, res_codex_proj.stderr
    resolved_proj = _resolve(project, real_home, bin_dir)
    assert resolved_proj["cli"] == "codex"
    assert resolved_proj["profile"] is None

    res_prune = _run_cli(
        ["set", "programmer", "hydrogen", "xhigh"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )
    assert res_prune.returncode == 0, res_prune.stderr
    updated_global = json.loads(global_cfg_path.read_text(encoding="utf-8"))
    assert updated_global["overrides"]["programmer"] == {
        "model": "hydrogen",
        "effort": "xhigh",
    }
    assert "profile" not in updated_global["overrides"]["programmer"]


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(
            ["set", "programmer", "codex-gpt", "xhigh", "--profile", "p1"],
            id="positional",
        ),
        pytest.param(
            [
                "set",
                "programmer",
                "--provider",
                "codex",
                "--model",
                "codex-gpt",
                "--effort",
                "xhigh",
                "--profile",
                "p1",
            ],
            id="flags",
        ),
    ],
)
def test_fpg_se15_one_command_non_agy_model_with_profile_still_exits_one(
    tmp_path: Path, args: list[str]
) -> None:
    """Retired --profile flag on set is rejected with --profile error and creates no config file."""
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    bin_dir = tmp_path / "bin"
    real_home.mkdir()
    project.mkdir()
    _make_stub_bin(bin_dir, ("agy", "claude", "codex", "kiro-cli"))
    _make_pool(real_home, ("p1",))

    res = _run_cli(
        [*args, "--scope", "project"],
        cwd=project,
        real_home=real_home,
        path_dir=bin_dir,
    )

    assert res.returncode == 1, (res.stdout, res.stderr)
    assert "--profile" in res.stderr
    assert not (project / ".agents" / "config" / "personas.json").exists()
