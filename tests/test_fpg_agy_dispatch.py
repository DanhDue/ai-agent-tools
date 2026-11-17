"""Tests for pooled agy dispatch, quota rotation, preflight safety, and dev_config dispatch CLI.

Covers BDD Scenarios:
- FPG-HP-12: The profiles CLI and dispatch drive stub CLIs through the pool
- FPG-EC-07: Invalid pool changes are rejected and a launch without the ag_run helpers starts nothing
- FPG-FR-05: Dispatch rotates to the next profile only before any work started
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
POOL_SCRIPT = REPO_ROOT / "scripts" / "agy_profile_pool.py"
DISPATCH_SCRIPT = REPO_ROOT / "scripts" / "agy_dispatch.py"
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


def _dispatch_mod() -> ModuleType:
    return _load_module("agy_dispatch", DISPATCH_SCRIPT)


def _persona_mod() -> ModuleType:
    return _load_module("persona_config", PERSONA_CONFIG_SCRIPT)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


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


def _make_profile_dirs(real_home: Path, names: tuple[str, ...]) -> None:
    homes = real_home / "antigravity_homes"
    homes.mkdir(parents=True, exist_ok=True)
    for name in names:
        (homes / name).mkdir(parents=True, exist_ok=True)


def _healthy_fetcher(_profile: str) -> dict[str, Any]:
    return {
        "status": "ACTIVE",
        "gemini5h": {"fraction": 0.90, "resetTime": "2026-11-17T14:00:00Z"},
        "geminiWeekly": {"fraction": 0.80, "resetTime": "2026-11-22T00:00:00Z"},
        "argonWeekly": {"fraction": 0.80, "resetTime": "2026-11-22T00:00:00Z"},
    }


def _subproc_env(
    real_home: Path,
    *,
    home: Path | None = None,
    bin_dir: Path | None = None,
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
    if bin_dir is not None:
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    return env


def test_fpg_fr_05_dispatch_rotates_only_before_work_starts(tmp_path: Path) -> None:
    """FPG-FR-05: Quota failures rotate only when HEAD and git status (ignoring .vscode/settings.json) are unchanged."""
    pool_mod = _pool_mod()
    dispatch_mod = _dispatch_mod()
    persona_mod = _persona_mod()
    real_home = tmp_path / "real_home"
    repo = tmp_path / "repo"
    _make_profile_dirs(real_home, ("p1", "p2"))
    _init_git_repo(repo)
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("implement feature\n", encoding="utf-8")

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

    binding = persona_mod.resolve_persona("programmer", repo, real_home=real_home)
    owner = {"repo": "repo", "epic": "e1", "task": "t1", "slot": 1, "role": "runner"}

    # Case 1: p1 fails with quota stderr and clean tree (only .vscode/settings.json changed) -> rotates to p2 and succeeds
    calls_1: list[str | None] = []

    def launcher_rotate(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        stdin_text: str,
        profile: str | None,
        via_ag_run: bool,
    ) -> tuple[int, str, str]:
        _ = (argv, env, stdin_text, via_ag_run)
        calls_1.append(profile)
        if profile == "p1":
            (cwd / ".vscode").mkdir(exist_ok=True)
            (cwd / ".vscode" / "settings.json").write_text("{}\n", encoding="utf-8")
            return (1, "", "RESOURCE_EXHAUSTED: quota exceeded")
        return (0, "done\n", "")

    res1 = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=repo,
        log=tmp_path / "run1.log",
        owner=owner,
        real_home=real_home,
        host_profile="px",
        launcher=launcher_rotate,
        fetcher=_healthy_fetcher,
        resident_probe=lambda _p: False,
        preflight=lambda: 0,
    )
    assert res1.status == "ok"
    assert res1.profile_used == "p2"
    assert res1.attempts == 2
    assert calls_1 == ["p1", "p2"]
    leases_1 = json.loads(
        (real_home / ".d3nexus" / "agy_profile_leases.json").read_text(encoding="utf-8")
    )
    assert leases_1["profiles"]["p1"]["exhausted_until"] is not None
    assert leases_1["profiles"]["p1"]["leases"] == []
    assert leases_1["profiles"]["p2"]["leases"] == []

    # Clear exhaustion for Case 2: p1 fails with quota stderr AFTER creating a commit -> quota_midrun, no retry
    pool_mod.clear_exhausted(real_home=real_home)
    calls_2: list[str | None] = []

    def launcher_midrun(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        stdin_text: str,
        profile: str | None,
        via_ag_run: bool,
    ) -> tuple[int, str, str]:
        _ = (argv, env, stdin_text, via_ag_run)
        calls_2.append(profile)
        (cwd / "work.txt").write_text("work\n", encoding="utf-8")
        subprocess.run(["git", "add", "work.txt"], cwd=cwd, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "partial work"], cwd=cwd, check=True
        )
        return (1, "", "RESOURCE_EXHAUSTED: quota exceeded")

    res2 = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=repo,
        log=tmp_path / "run2.log",
        owner=owner,
        real_home=real_home,
        host_profile="px",
        launcher=launcher_midrun,
        fetcher=_healthy_fetcher,
        resident_probe=lambda _p: False,
        preflight=lambda: 0,
    )
    assert res2.status == "quota_midrun"
    assert res2.profile_used == "p1"
    assert res2.attempts == 1
    assert calls_2 == ["p1"]
    leases_2 = json.loads(
        (real_home / ".d3nexus" / "agy_profile_leases.json").read_text(encoding="utf-8")
    )
    assert leases_2["profiles"]["p1"]["exhausted_until"] is not None
    assert leases_2["profiles"]["p1"]["leases"] == []

    # Clear exhaustion for Case 3: every profile fails with quota stderr and unchanged tree -> no_profile (pool_exhausted)
    pool_mod.clear_exhausted(real_home=real_home)
    calls_3: list[str | None] = []

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
        calls_3.append(profile)
        return (1, "", "RESOURCE_EXHAUSTED: quota exceeded")

    res3 = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=repo,
        log=tmp_path / "run3.log",
        owner=owner,
        real_home=real_home,
        host_profile="px",
        launcher=launcher_all_quota,
        fetcher=_healthy_fetcher,
        resident_probe=lambda _p: False,
        preflight=lambda: 0,
    )
    assert res3.status == "no_profile"
    assert res3.reason == "pool_exhausted"
    assert res3.attempts == 2
    assert calls_3 == ["p1", "p2"]
    assert len(res3.report) >= 1
    st3 = pool_mod.pool_status(real_home=real_home)
    assert all(entry["leased_by"] == [] for entry in st3["profiles"])

    # Clear exhaustion for Case 4: task failure does NOT mark p1 exhausted and releases lease
    pool_mod.clear_exhausted(real_home=real_home)
    res4 = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=repo,
        log=tmp_path / "run4.log",
        owner=owner,
        real_home=real_home,
        host_profile="px",
        launcher=lambda argv, **kw: (1, "3 failed, 10 passed\n", ""),
        fetcher=_healthy_fetcher,
        resident_probe=lambda _p: False,
        preflight=lambda: 0,
    )
    assert res4.status == "task_failure"
    assert res4.attempts == 1
    leases_4 = json.loads(
        (real_home / ".d3nexus" / "agy_profile_leases.json").read_text(encoding="utf-8")
    )
    assert leases_4["profiles"]["p1"]["exhausted_until"] is None
    assert leases_4["profiles"]["p1"]["leases"] == []


def test_fpg_ec_07_preflight_failure_launches_nothing(tmp_path: Path) -> None:
    """FPG-EC-07: Non-zero preflight releases lease, launches nothing, and returns preflight_failed."""
    pool_mod = _pool_mod()
    dispatch_mod = _dispatch_mod()
    persona_mod = _persona_mod()
    real_home = tmp_path / "real_home"
    repo = tmp_path / "repo"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    _make_profile_dirs(real_home, ("p1",))
    _init_git_repo(repo)
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("hello\n", encoding="utf-8")

    # Stub zsh fails preflight
    zsh_stub = bin_dir / "zsh"
    zsh_stub.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    zsh_stub.chmod(0o755)

    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {"schema_version": 1, "pool": [{"profile": "p1", "priority": 1}]},
    )

    launched: list[list[str]] = []

    def fail_if_called(argv: list[str], **kw: Any) -> tuple[int, str, str]:
        _ = kw
        launched.append(argv)
        return (0, "", "")

    binding = persona_mod.resolve_persona("programmer", repo, real_home=real_home)
    old_path = os.environ.get("PATH", "")
    env_stub_path = f"{bin_dir}:{old_path}"
    res = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=repo,
        log=tmp_path / "pf.log",
        owner={"epic": "e1", "task": "t1", "slot": 1, "role": "orchestrator"},
        real_home=real_home,
        extra_env={"PATH": env_stub_path},
        host_profile="other",
        launcher=fail_if_called,
        fetcher=_healthy_fetcher,
        resident_probe=lambda _p: False,
    )
    assert res.status == "preflight_failed"
    assert res.attempts == 0
    assert launched == []
    st = pool_mod.pool_status(real_home=real_home)
    assert st["profiles"][0]["leased_by"] == []


class TestFpgHp12_Integration:
    """Tier C integration runner tests for FPG-HP-12 profiles CLI and pooled dispatch."""

    def test_fpg_hp_12_profiles_cli_and_dispatch_with_stub_clis(
        self, tmp_path: Path
    ) -> None:
        """FPG-HP-12: profiles CLI and dispatch drive stub zsh/ag_run and direct agy through the pool."""
        real_home = tmp_path / "real_home"
        repo = tmp_path / "repo"
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(parents=True)
        _make_profile_dirs(real_home, ("p1", "p2"))
        _init_git_repo(repo)
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("implement task\n", encoding="utf-8")

        zsh_records = tmp_path / "zsh_calls.jsonl"
        agy_records = tmp_path / "agy_calls.jsonl"

        (bin_dir / "zsh").write_text(
            f"""#!{sys.executable}
import json, os, sys
rec = {{"argv": sys.argv[1:], "HOME": os.environ.get("HOME"), "REAL_HOME": os.environ.get("REAL_HOME"), "AGY_PROFILE": os.environ.get("AGY_PROFILE"), "stdin": sys.stdin.read() if not sys.stdin.isatty() else ""}}
with open({str(zsh_records)!r}, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec) + "\\n")
sys.exit(0)
""",
            encoding="utf-8",
        )
        (bin_dir / "zsh").chmod(0o755)

        (bin_dir / "agy").write_text(
            f"""#!{sys.executable}
import json, os, sys
rec = {{"argv": sys.argv[1:], "HOME": os.environ.get("HOME"), "REAL_HOME": os.environ.get("REAL_HOME"), "AGY_PROFILE": os.environ.get("AGY_PROFILE"), "stdin": sys.stdin.read() if not sys.stdin.isatty() else ""}}
with open({str(agy_records)!r}, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec) + "\\n")
sys.exit(0)
""",
            encoding="utf-8",
        )
        (bin_dir / "agy").chmod(0o755)

        env_host_x = _subproc_env(real_home, bin_dir=bin_dir, agy_profile="host_x")

        for cmd in [
            ["profiles", "add", "p1", "--priority", "1"],
            ["profiles", "add", "p2", "--priority", "2"],
        ]:
            p = subprocess.run(
                [
                    sys.executable,
                    str(DEV_CONFIG_SCRIPT),
                    "--project-root",
                    str(repo),
                    *cmd,
                ],
                env=env_host_x,
                capture_output=True,
                text=True,
                check=False,
            )
            assert p.returncode == 0, p.stderr

        list_p = subprocess.run(
            [
                sys.executable,
                str(DEV_CONFIG_SCRIPT),
                "--project-root",
                str(repo),
                "profiles",
                "list",
                "--json",
            ],
            env=env_host_x,
            capture_output=True,
            text=True,
            check=False,
        )
        assert list_p.returncode == 0
        list_data = json.loads(list_p.stdout)
        assert [entry["profile"] for entry in list_data["profiles"]] == ["p1", "p2"]
        assert all(entry["leased_by"] == [] for entry in list_data["profiles"])

        log1 = tmp_path / "run.log"
        dispatch_runner = f"""
import importlib.util, sys
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
pool_mod = load("agy_profile_pool", {str(POOL_SCRIPT)!r})
load("agy_dispatch", {str(DISPATCH_SCRIPT)!r})
dc = load("dev_config", {str(DEV_CONFIG_SCRIPT)!r})
pool_mod.default_fetcher = lambda _p: {{
    "status": "ACTIVE",
    "gemini5h": {{"fraction": 0.90, "resetTime": "2026-11-17T14:00:00Z"}},
    "geminiWeekly": {{"fraction": 0.80, "resetTime": "2026-11-22T00:00:00Z"}},
}}
pool_mod.default_resident_probe = lambda _p: False
raise SystemExit(dc.main(sys.argv[1:]))
"""
        disp1 = subprocess.run(
            [
                sys.executable,
                "-c",
                dispatch_runner,
                "dispatch",
                "--persona",
                "programmer",
                "--prompt-file",
                str(prompt_file),
                "--cwd",
                str(repo),
                "--log",
                str(log1),
                "--epic",
                "e1",
                "--task",
                "t1",
            ],
            env=env_host_x,
            capture_output=True,
            text=True,
            check=False,
        )
        assert disp1.returncode == 0, disp1.stderr
        res1 = json.loads(disp1.stdout)
        assert res1["status"] == "ok"
        assert res1["profile_used"] == "p1"

        zsh_calls = [
            json.loads(line)
            for line in zsh_records.read_text(encoding="utf-8").splitlines()
        ]
        assert len(zsh_calls) == 2
        assert "typeset -f _ag_link_ok _ag_rel_link ag_run" in " ".join(
            zsh_calls[0]["argv"]
        )
        launch_argv = zsh_calls[1]["argv"]
        assert any("ag_run" in tok for tok in launch_argv)
        for tok in ("p1", "--model", "gemini-4-hydrogen-xhigh", "--effort", "xhigh"):
            assert tok in launch_argv

        log1_text = log1.read_text(encoding="utf-8").strip()
        assert log1_text.startswith("dispatch-profile: p1")
        assert log1_text.endswith("agy-exit=0")

        list_after = json.loads(
            subprocess.run(
                [
                    sys.executable,
                    str(DEV_CONFIG_SCRIPT),
                    "--project-root",
                    str(repo),
                    "profiles",
                    "list",
                    "--json",
                ],
                env=env_host_x,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )
        assert list_after["profiles"][0]["leased_by"] == []

        # Second dispatch with host profile == p1 -> direct agy, stub zsh NOT called again, HOME left unchanged
        zsh_records.unlink()
        host_p1_home = real_home / "antigravity_homes" / "p1"
        env_p1 = _subproc_env(real_home, home=host_p1_home, bin_dir=bin_dir)
        log2 = tmp_path / "run2.log"
        disp2 = subprocess.run(
            [
                sys.executable,
                "-c",
                dispatch_runner,
                "dispatch",
                "--persona",
                "programmer",
                "--prompt-file",
                str(prompt_file),
                "--cwd",
                str(repo),
                "--log",
                str(log2),
                "--epic",
                "e1",
                "--task",
                "t1",
            ],
            env=env_p1,
            capture_output=True,
            text=True,
            check=False,
        )
        assert disp2.returncode == 0, disp2.stderr
        assert not zsh_records.exists()
        agy_calls = [
            json.loads(line)
            for line in agy_records.read_text(encoding="utf-8").splitlines()
        ]
        assert len(agy_calls) == 1
        assert agy_calls[0]["HOME"] == str(host_p1_home)
        assert "--model" in agy_calls[0]["argv"]
        assert "gemini-4-hydrogen-xhigh" in agy_calls[0]["argv"]

    def test_fpg_hp_12_dispatch_exit_codes_heartbeat_and_non_quota_unavailable(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """FPG-HP-12: cmd_dispatch exit codes (0/1/2), heartbeat refresh during run, and non-quota failure without rotation."""
        import time

        pool_mod = _pool_mod()
        _dispatch_mod()
        dc = _load_module("dev_config", DEV_CONFIG_SCRIPT)

        real_home = tmp_path / "real_home"
        repo = tmp_path / "repo"
        _make_profile_dirs(real_home, ("p1", "p2"))
        _init_git_repo(repo)
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("work\n", encoding="utf-8")

        _write_json(
            real_home / ".d3nexus" / "agy_profiles.json",
            {
                "schema_version": 1,
                "pool": [
                    {"profile": "p1", "priority": 1},
                    {"profile": "p2", "priority": 2},
                ],
                "heartbeat_seconds": 0.05,
            },
        )

        hb_calls = 0
        orig_hb = pool_mod.heartbeat

        def spy_hb(
            owner_id: str, *, real_home: Path | str | None = None, now: Any = None
        ) -> bool:
            nonlocal hb_calls
            hb_calls += 1
            return bool(orig_hb(owner_id, real_home=real_home, now=now))

        monkeypatch.setattr(pool_mod, "heartbeat", spy_hb)

        def slow_launcher(argv: list[str], **kw: Any) -> tuple[int, str, str]:
            _ = (argv, kw)
            time.sleep(0.18)
            return (0, "ok\n", "")

        rc_ok = dc.cmd_dispatch(
            repo,
            persona="programmer",
            prompt_file=prompt_file,
            cwd=repo,
            log=tmp_path / "hb.log",
            real_home=real_home,
            fetcher=_healthy_fetcher,
            resident_probe=lambda _p: False,
            launcher=slow_launcher,
            preflight=lambda: 0,
        )
        assert rc_ok == 0
        assert hb_calls >= 2
        _ = json.loads(capsys.readouterr().out)

        # Non-quota model_unavailable (401 Unauthorized) does not rotate and exits 1
        auth_calls: list[str | None] = []

        def auth_fail_launcher(
            argv: list[str], *, profile: str | None = None, **kw: Any
        ) -> tuple[int, str, str]:
            _ = (argv, kw)
            auth_calls.append(profile)
            return (1, "", "401 Unauthorized: please log in")

        rc_auth = dc.cmd_dispatch(
            repo,
            persona="programmer",
            prompt_file=prompt_file,
            cwd=repo,
            log=tmp_path / "auth.log",
            real_home=real_home,
            fetcher=_healthy_fetcher,
            resident_probe=lambda _p: False,
            launcher=auth_fail_launcher,
            preflight=lambda: 0,
        )
        assert rc_auth == 1
        assert len(auth_calls) == 1
        auth_out = json.loads(capsys.readouterr().out)
        assert auth_out["status"] == "model_unavailable"

        # Exhausted pool exits 2 with report (clear cached quota from previous run first)
        pool_mod.clear_exhausted(real_home=real_home)
        rc_exhausted = dc.cmd_dispatch(
            repo,
            persona="programmer",
            prompt_file=prompt_file,
            cwd=repo,
            log=tmp_path / "ex.log",
            real_home=real_home,
            fetcher=lambda _p: {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.01, "resetTime": "2026-11-17T12:00:00Z"},
                "geminiWeekly": {"fraction": 0.50, "resetTime": "2026-11-22T00:00:00Z"},
            },
            resident_probe=lambda _p: False,
            launcher=slow_launcher,
            preflight=lambda: 0,
        )
        assert rc_exhausted == 2
        ex_out = json.loads(capsys.readouterr().out)
        assert ex_out["status"] == "no_profile"
        assert isinstance(ex_out["report"], list) and ex_out["report"]

        # Exception during launcher still releases lease in finally
        pool_mod.clear_exhausted(real_home=real_home)

        def boom_launcher(argv: list[str], **kw: Any) -> tuple[int, str, str]:
            _ = (argv, kw)
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            dc.cmd_dispatch(
                repo,
                persona="programmer",
                prompt_file=prompt_file,
                cwd=repo,
                log=tmp_path / "boom.log",
                real_home=real_home,
                fetcher=_healthy_fetcher,
                resident_probe=lambda _p: False,
                launcher=boom_launcher,
                preflight=lambda: 0,
            )
        st_after_boom = pool_mod.pool_status(real_home=real_home)
        assert all(entry["leased_by"] == [] for entry in st_after_boom["profiles"])


def test_fpg_fr_05_non_git_cwd_and_empty_pool_and_non_agy_dispatch(
    tmp_path: Path,
) -> None:
    """FPG-FR-05: Empty pool runs directly without lease, non-git cwd counts as changed, non-agy bypasses pool."""
    _pool_mod()
    dispatch_mod = _dispatch_mod()
    persona_mod = _persona_mod()
    real_home = tmp_path / "real_home"
    non_git = tmp_path / "plain_dir"
    non_git.mkdir()
    real_home.mkdir()
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("hi\n", encoding="utf-8")

    # Empty pool: runs once with no lease file created
    binding = persona_mod.resolve_persona("programmer", non_git, real_home=real_home)
    res_empty = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=non_git,
        log=tmp_path / "empty.log",
        owner={"epic": "e", "task": "t", "slot": 1, "role": "runner"},
        real_home=real_home,
        host_profile="host_x",
        launcher=lambda argv, **kw: (0, "ok\n", ""),
    )
    assert res_empty.status == "ok"
    assert res_empty.attempts == 1
    assert not (real_home / ".d3nexus" / "agy_profile_leases.json").exists()

    # Non-git cwd with pool -> quota error does NOT rotate (counts as changed -> quota_midrun)
    _make_profile_dirs(real_home, ("p1", "p2"))
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": "p1", "priority": 1},
                {"profile": "p2", "priority": 2},
            ],
            "agy_extra_args": ["--dangerously-skip-permissions"],
        },
    )
    seen_argvs: list[list[str]] = []

    def launcher_non_git(argv: list[str], **kw: Any) -> tuple[int, str, str]:
        _ = kw
        seen_argvs.append(argv)
        return (1, "", "429 Too Many Requests")

    res_ng = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=non_git,
        log=tmp_path / "nongit.log",
        owner={"epic": "e", "task": "t", "slot": 1, "role": "runner"},
        real_home=real_home,
        host_profile="px",
        launcher=launcher_non_git,
        fetcher=_healthy_fetcher,
        resident_probe=lambda _p: False,
        preflight=lambda: 0,
    )
    assert res_ng.status == "quota_midrun"
    assert res_ng.attempts == 1
    assert "--dangerously-skip-permissions" in seen_argvs[0]

    # Non-agy binding never touches pool
    claude_binding = persona_mod.resolve_persona(
        "ai_architect_reviewer",
        non_git,
        cli_overrides={"model": "claude-opus", "effort": "high"},
        real_home=real_home,
    )
    res_claude = dispatch_mod.run_on_pool(
        claude_binding,
        "read-only",
        prompt_file=prompt_file,
        cwd=non_git,
        log=tmp_path / "claude.log",
        owner={"epic": "e", "task": "t", "slot": 1, "role": "orchestrator"},
        real_home=real_home,
        launcher=lambda argv, **kw: (0, f"ran {argv[0]}\n", ""),
    )
    assert res_claude.status == "ok"
    assert res_claude.profile_used is None
    assert res_claude.attempts == 1


@pytest.mark.parametrize(
    ("reason", "skipped", "pool_state", "exhausted_until", "exhausted_reason"),
    [
        ("pool_busy", {"p1": "resident_process"}, "ok", None, None),
        (
            "pool_exhausted",
            {"p1": "exhausted"},
            "exhausted",
            "2026-11-17T12:00:00Z",
            "5h",
        ),
    ],
)
def test_no_profile_report_distinguishes_resident_busy_from_exhausted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
    skipped: dict[str, str],
    pool_state: str,
    exhausted_until: str | None,
    exhausted_reason: str | None,
) -> None:
    """S3: A resident_process pool_busy outcome must report busy + wait/free steps, never exhausted quota."""
    pool_mod = _pool_mod()
    dispatch_mod = _dispatch_mod()
    persona_mod = _persona_mod()
    real_home = tmp_path / "real_home"
    repo = tmp_path / "repo"
    _make_profile_dirs(real_home, ("p1",))
    repo.mkdir(parents=True)
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("task\n", encoding="utf-8")
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {"schema_version": 1, "pool": [{"profile": "p1", "priority": 1}]},
    )

    injected_acq = pool_mod.Acquisition(
        profile=None,
        via_ag_run=False,
        owner_id="owner-1",
        skipped=skipped,
        reason=reason,
    )
    injected_status = {
        "state": pool_state,
        "profiles": [
            {
                "profile": "p1",
                "priority": 1,
                "max_concurrent": 1,
                "leased_by": [],
                "exhausted_until": exhausted_until,
                "exhausted_reason": exhausted_reason,
                "quota": None,
            }
        ],
        "earliest_reset": exhausted_until,
    }
    monkeypatch.setattr(pool_mod, "acquire", lambda *_a, **_kw: injected_acq)
    monkeypatch.setattr(
        pool_mod, "pool_status", lambda *_a, **_kw: dict(injected_status)
    )

    binding = persona_mod.resolve_persona("programmer", repo, real_home=real_home)
    res = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=repo,
        log=tmp_path / "dispatch.log",
        owner={"repo": "repo", "epic": "e1", "task": "t1", "slot": 1, "role": "runner"},
        real_home=real_home,
        host_profile="other",
        wait_seconds=15,
    )

    assert res.status == "no_profile"
    assert res.reason == reason
    joined = "\n".join(res.report).lower()
    if reason == "pool_busy":
        assert "busy" in joined
        assert "resident" in joined
        assert "p1" in joined
        assert "wait" in joined
        assert any(tok in joined for tok in ("free", "close", "terminat", "pkill"))
        assert "out of quota" not in joined
        assert "exhausted" not in joined
    else:
        assert res.report[0] == "Stopped: all agy profiles are out of quota."
        assert "- p1: 5-hour limit reached (resets 2026-11-17T12:00:00Z)" in res.report


@pytest.mark.parametrize("host_profile", ["p1", "other"])
def test_run_on_pool_enforces_timeout_and_process_group_isolation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    host_profile: str,
) -> None:
    """Pooled dispatch isolates child process group, enforces timeout_seconds, kills grandchildren, and releases lease."""
    import signal
    import time

    pool_mod = _pool_mod()
    dispatch_mod = _dispatch_mod()
    persona_mod = _persona_mod()

    real_home = tmp_path / "real_home"
    repo = tmp_path / "repo"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    _make_profile_dirs(real_home, ("p1",))
    _init_git_repo(repo)
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("long task\n", encoding="utf-8")

    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [{"profile": "p1", "priority": 1}],
            "heartbeat_seconds": 0.05,
            "lease_ttl_seconds": 2,
        },
    )

    pgid_file = tmp_path / f"pgid_{host_profile}.txt"
    gc_pid_file = tmp_path / f"gc_pid_{host_profile}.txt"

    (bin_dir / "agy").write_text(
        f"""#!/bin/sh
sleep 3 &
echo "$!" > {str(gc_pid_file)!r}
ps -o pid=,pgid= -p $$ > {str(pgid_file)!r}
wait
""",
        encoding="utf-8",
    )
    (bin_dir / "agy").chmod(0o755)
    (bin_dir / "zsh").write_text(
        f"""#!/bin/sh
case "$*" in
  *typeset*) exit 0 ;;
esac
sleep 3 &
echo "$!" > {str(gc_pid_file)!r}
ps -o pid=,pgid= -p $$ > {str(pgid_file)!r}
wait
""",
        encoding="utf-8",
    )
    (bin_dir / "zsh").chmod(0o755)

    hb_calls = 0
    orig_hb = pool_mod.heartbeat

    def spy_hb(
        owner_id: str, *, real_home: Path | str | None = None, now: Any = None
    ) -> bool:
        nonlocal hb_calls
        hb_calls += 1
        return bool(orig_hb(owner_id, real_home=real_home, now=now))

    monkeypatch.setattr(pool_mod, "heartbeat", spy_hb)
    binding = persona_mod.resolve_persona("programmer", repo, real_home=real_home)
    env_extra = {"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"}

    t0 = time.monotonic()
    try:
        res = dispatch_mod.run_on_pool(
            binding,
            "write",
            prompt_file=prompt_file,
            cwd=repo,
            log=tmp_path / f"timeout_{host_profile}.log",
            owner={
                "repo": "repo",
                "epic": "e1",
                "task": "t1",
                "slot": 1,
                "role": "runner",
            },
            real_home=real_home,
            extra_env=env_extra,
            host_profile=host_profile,
            fetcher=_healthy_fetcher,
            resident_probe=lambda _p: False,
            timeout_seconds=0.5,
        )
    finally:
        elapsed = time.monotonic() - t0

    assert res.status == "task_failure"
    assert res.exit_code == 124
    assert res.reason == "timeout"
    assert any("Process timeout:" in line for line in res.report)
    assert elapsed < 1.5

    parts = pgid_file.read_text(encoding="utf-8").strip().split()
    assert len(parts) == 2
    child_pid, child_pgid = int(parts[0]), int(parts[1])
    assert child_pgid == child_pid
    assert child_pgid != os.getpgrp()

    gc_pid = int(gc_pid_file.read_text(encoding="utf-8").strip())
    for _ in range(10):
        try:
            os.kill(gc_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        os.kill(gc_pid, signal.SIGKILL)
        pytest.fail(f"Grandchild process {gc_pid} survived process-group timeout kill")

    st = pool_mod.pool_status(real_home=real_home)
    assert st["profiles"][0]["leased_by"] == []

    hb_after = hb_calls
    time.sleep(0.15)
    assert hb_calls == hb_after


@pytest.mark.parametrize(
    ("log_rel", "commit_log"),
    [
        ("run.log", False),
        (".devtool/dispatch.log", False),
        ("run.log", True),
    ],
    ids=["untracked_root_log", "untracked_devtool_log", "committed_log"],
)
def test_fpg_fr_05_log_inside_cwd_is_not_agent_work(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    log_rel: str,
    commit_log: bool,
) -> None:
    """FPG-FR-05: Writing the attempt log inside cwd must not count as agent work before rotation."""
    dispatch_mod = _dispatch_mod()
    persona_mod = _persona_mod()
    real_home = tmp_path / "real_home"
    repo = tmp_path / "repo"
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("REAL_HOME", str(real_home))
    _make_profile_dirs(real_home, ("p1", "p2"))
    _init_git_repo(repo)
    if commit_log:
        log_file = repo / log_rel
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text("previous\n", encoding="utf-8")
        subprocess.run(["git", "add", "-f", log_rel], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "track log"], cwd=repo, check=True)

    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("implement feature\n", encoding="utf-8")
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

    calls: list[str | None] = []

    def launcher(
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
        if profile == "p1":
            return (1, "", "RESOURCE_EXHAUSTED: quota exceeded")
        return (0, "done\n", "")

    binding = persona_mod.resolve_persona("programmer", repo, real_home=real_home)
    res = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=repo,
        log=repo / log_rel,
        owner={"repo": "repo", "epic": "e1", "task": "t1", "slot": 1, "role": "runner"},
        real_home=real_home,
        host_profile="px",
        launcher=launcher,
        fetcher=_healthy_fetcher,
        resident_probe=lambda _p: False,
        preflight=lambda: 0,
    )
    assert res.status == "ok"
    assert res.profile_used == "p2"
    assert res.attempts == 2
    assert calls == ["p1", "p2"]
    assert (repo / log_rel).is_file()


def test_fpg_fr_05_work_file_plus_log_inside_cwd_stays_quota_midrun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FPG-FR-05: Agent file edits alongside an in-repo attempt log still halt with quota_midrun."""
    dispatch_mod = _dispatch_mod()
    persona_mod = _persona_mod()
    real_home = tmp_path / "real_home"
    repo = tmp_path / "repo"
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("REAL_HOME", str(real_home))
    _make_profile_dirs(real_home, ("p1", "p2"))
    _init_git_repo(repo)
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("implement feature\n", encoding="utf-8")
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

    calls: list[str | None] = []

    def launcher(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        stdin_text: str,
        profile: str | None,
        via_ag_run: bool,
    ) -> tuple[int, str, str]:
        _ = (argv, env, stdin_text, via_ag_run)
        calls.append(profile)
        (cwd / "work.txt").write_text("partial\n", encoding="utf-8")
        return (1, "", "RESOURCE_EXHAUSTED: quota exceeded")

    binding = persona_mod.resolve_persona("programmer", repo, real_home=real_home)
    res = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=repo,
        log=repo / "run.log",
        owner={"repo": "repo", "epic": "e1", "task": "t1", "slot": 1, "role": "runner"},
        real_home=real_home,
        host_profile="px",
        launcher=launcher,
        fetcher=_healthy_fetcher,
        resident_probe=lambda _p: False,
        preflight=lambda: 0,
    )
    assert res.status == "quota_midrun"
    assert res.profile_used == "p1"
    assert res.attempts == 1
    assert calls == ["p1"]
