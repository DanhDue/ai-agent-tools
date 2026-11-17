"""Dashboard sync tests for personas, checkpoints, halts, agy pool alerts and English-only docs.

Covers BDD scenarios:
- FPG-HP-07: Payload carries persona bindings, the latest checkpoint and low-quota state
- FPG-HP-13: Dashboard shows which profile each orchestrator holds and alerts when the agy pool is exhausted
- FPG-EC-05: An invalid persona configuration degrades to a dashboard warning
- FPG-ST-04: Quota, model and escalation stops render as human action on the dashboard
"""

from __future__ import annotations

import builtins
from collections.abc import Iterator
import contextlib
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from typing import Any
import urllib.request

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
CHECK_TASKS_SCRIPTS = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
DASHBOARD_HTML = (
    REPO_ROOT
    / "skills"
    / "check-tasks"
    / "resources"
    / "dashboard"
    / "tasks_dashboard.html"
)
for _p in (str(SCRIPTS_DIR), str(CHECK_TASKS_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _state_envelope  # type: ignore[import-not-found]  # noqa: E402
import check_tasks  # type: ignore[import-not-found]  # noqa: E402
import tasks_server  # type: ignore[import-not-found]  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_host_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point HOME and REAL_HOME at a temporary directory and drop profile variables."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("REAL_HOME", str(home))
    monkeypatch.delenv("AGY_PROFILE", raising=False)
    monkeypatch.delenv("ANTIGRAVITY_PROFILE", raising=False)
    # CLI lookups must not stat shims that live inside host Antigravity profiles
    safe_path = os.pathsep.join(
        entry
        for entry in os.environ.get("PATH", "").split(os.pathsep)
        if "/antigravity_homes" not in entry
    )
    monkeypatch.setenv("PATH", safe_path)
    monkeypatch.setattr(
        check_tasks, "discover_antigravity_profiles", lambda *a, **k: []
    )
    return home


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True)


def _init_repo(repo: Path) -> Path:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@fpg.local")
    _git(repo, "config", "user.name", "FPG Tester")
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "Initial commit")
    return repo


def _utc(delta: timedelta = timedelta(0)) -> str:
    return (datetime.now(timezone.utc) + delta).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _d3nexus(home: Path) -> Path:
    return home / ".d3nexus"


def _set_heartbeat_halt(repo: Path, epic: str, token: str) -> None:
    safe = _state_envelope._sanitize_epic_slug(epic)

    def _mutate(state: dict[str, Any]) -> None:
        state["halt_reason"] = token

    _state_envelope.run_state_transaction(
        repo,
        f"{safe}.heartbeat.json",
        _mutate,
        default=_state_envelope._default_heartbeat_payload(epic),
    )


def _seed_checkpoint(repo: Path, epic: str, **fields: Any) -> None:
    block: dict[str, Any] = {"event": "wave_merged", "next_step": "start wave 3"}
    block.update(fields)
    _state_envelope.update_epic_checkpoint(repo, epic, block)


@contextlib.contextmanager
def _running_server(workspace: Path, pid_file: Path) -> Iterator[int]:
    server = tasks_server.TasksServer(
        host="127.0.0.1",
        port=19350,
        workspace_root=workspace,
        pid_file=pid_file,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    try:
        yield int(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3.0)


def _write_pool(home: Path, profiles: list[str]) -> None:
    _write_json(
        _d3nexus(home) / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": name, "priority": idx + 1, "max_concurrent": 1}
                for idx, name in enumerate(profiles)
            ],
        },
    )


def _lease(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "owner_id": "owner-1",
        "repo": "demo_repo",
        "epic": "e1",
        "task": "t1",
        "slot": 1,
        "role": "orchestrator",
        "launch": "ag_run",
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "acquired_at": _utc(),
        "heartbeat_at": _utc(),
    }
    base.update(overrides)
    return base


def test_fpg_hp_13_dashboard_shows_profile_holders_and_alerts_when_pool_is_exhausted(
    tmp_path: Path, _isolated_host_env: Path
) -> None:
    """[FPG-HP-13] [Tier A - Unit] The dashboard names each profile holder and alerts when every agy profile is out of quota."""
    repo = _init_repo(tmp_path / "demo_repo")
    home = _isolated_host_env
    _write_pool(home, ["p1", "p2"])
    p2_until = _utc(timedelta(days=3))
    leases_path = _d3nexus(home) / "agy_profile_leases.json"
    quota = {
        "gemini5h": {"fraction": 0.4, "resetTime": _utc(timedelta(hours=2))},
        "geminiWeekly": {"fraction": 0.0, "resetTime": p2_until},
    }
    _write_json(
        leases_path,
        {
            "schema_version": 1,
            "profiles": {
                "p1": {"leases": [_lease()]},
                "p2": {
                    "leases": [],
                    "exhausted_until": p2_until,
                    "exhausted_reason": "weekly",
                    "quota": quota,
                },
            },
        },
    )

    busy = check_tasks.scan_repo(repo)

    by_name = {p["profile"]: p for p in busy.agy_profiles}
    assert set(by_name) == {"p1", "p2"}
    holder = by_name["p1"]["leased_by"][0]
    assert (holder["epic"], holder["task"], holder["slot"]) == ("e1", "t1", 1)
    assert holder["repo"] == "demo_repo"
    assert holder["role"] == "orchestrator"
    assert by_name["p2"]["leased_by"] == []
    assert by_name["p2"]["exhausted_until"] == p2_until
    assert by_name["p2"]["exhausted_reason"] == "weekly"
    assert by_name["p2"]["quota_5h"]["fraction"] == 0.4
    assert by_name["p2"]["quota_weekly"]["fraction"] == 0.0
    assert busy.agy_pool is not None and busy.agy_pool["state"] == "busy"
    assert not any("out of quota" in b["reason"] for b in busy.action_blockers)
    assert busy.is_human_action_required is False
    assert any("p1" in n and "in use" in n for n in busy.notices)

    p1_until = _utc(timedelta(hours=2))
    _write_json(
        leases_path,
        {
            "schema_version": 1,
            "profiles": {
                "p1": {
                    "leases": [],
                    "exhausted_until": p1_until,
                    "exhausted_reason": "5h",
                },
                "p2": {
                    "leases": [],
                    "exhausted_until": p2_until,
                    "exhausted_reason": "weekly",
                    "quota": quota,
                },
            },
        },
    )

    exhausted = check_tasks.scan_repo(repo)

    assert exhausted.agy_pool is not None and exhausted.agy_pool["state"] == "exhausted"
    assert exhausted.is_human_action_required is True
    pool_entries = [
        b for b in exhausted.action_blockers if "out of quota" in b["reason"]
    ]
    assert len(pool_entries) == 1
    reason = pool_entries[0]["reason"]
    assert "all agy profiles are out of quota" in reason
    assert "- p1: 5-hour limit reached" in reason
    assert "- p2: weekly limit reached" in reason
    assert f"Earliest reset: {p1_until}." in reason
    assert "/d3nexus:dev-config set programmer codex-gpt xhigh" in reason
    assert not any("p1" in n and "in use" in n for n in exhausted.notices)


def test_fpg_hp_13_unreadable_pool_files_never_raise(
    tmp_path: Path, _isolated_host_env: Path
) -> None:
    """[FPG-HP-13] An unreadable or invalid pool configuration degrades to a notice."""
    repo = _init_repo(tmp_path / "demo_repo")
    pool_path = _d3nexus(_isolated_host_env) / "agy_profiles.json"
    pool_path.parent.mkdir(parents=True, exist_ok=True)
    pool_path.write_text("{not json", encoding="utf-8")

    meta = check_tasks.scan_repo(repo)

    assert meta.agy_pool is None
    assert meta.agy_profiles == []
    assert any("agy profile pool unavailable" in n for n in meta.notices)
    assert meta.is_human_action_required is False


def test_fpg_ec_05_invalid_persona_config_degrades_to_a_warning(
    tmp_path: Path, _isolated_host_env: Path
) -> None:
    """[FPG-EC-05] [Tier A - Unit] An invalid persona configuration degrades to a dashboard warning."""
    repo = _init_repo(tmp_path / "demo_repo")
    _write_json(repo / ".agents" / "config" / "personas.json", {"schema_version": 99})

    meta = check_tasks.scan_repo(repo)

    assert meta.name == "demo_repo"
    assert meta.persona_bindings == []
    assert meta.persona_config_error is not None
    assert "schema_version" in meta.persona_config_error


def test_fpg_ec_05_persona_module_load_failure_degrades_to_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[FPG-EC-05] A persona_config load failure is reported, never raised."""
    repo = _init_repo(tmp_path / "demo_repo")

    def _boom(name: str, *rel: str) -> Any:
        raise RuntimeError(f"cannot load {name}")

    monkeypatch.setattr(check_tasks, "_load_kit_module", _boom)

    meta = check_tasks.scan_repo(repo)

    assert meta.persona_bindings == []
    assert meta.persona_config_error is not None
    assert "cannot load persona_config" in meta.persona_config_error
    assert meta.low_quota is None


def _seed_epic_with_decision(
    repo: Path, epic: str, kind: str, reason: str, stage: str = "Stage 3"
) -> None:
    _state_envelope.record_pending_decision(repo, epic, reason, kind=kind, stage=stage)


def test_fpg_st_04_quota_model_and_escalation_stops_render_as_human_action(
    tmp_path: Path,
) -> None:
    """[FPG-ST-04] [Tier C - Integration] Quota, model and escalation stops render as human action on the dashboard."""
    quota_repo = _init_repo(tmp_path / "quota_repo")
    _seed_epic_with_decision(
        quota_repo,
        "quota_epic",
        "quota",
        "Stopped: quota too low\nprogrammer agy 5H=12.0%",
    )
    blocker_repo = _init_repo(tmp_path / "blocker_repo")
    _seed_epic_with_decision(
        blocker_repo, "blocker_epic", "blocker", "programmer model hydrogen unavailable"
    )
    halt_repo = _init_repo(tmp_path / "halt_repo")
    _seed_checkpoint(halt_repo, "halt_epic", event="turn_budget")
    _set_heartbeat_halt(halt_repo, "halt_epic", "FIX_PLAN_ESCALATE")
    warn_repo = _init_repo(tmp_path / "warn_repo")
    _seed_checkpoint(warn_repo, "warn_epic", warning="quota_unknown")

    quota_meta = check_tasks.scan_repo(quota_repo)
    blocker_meta = check_tasks.scan_repo(blocker_repo)
    halt_meta = check_tasks.scan_repo(halt_repo)
    warn_meta = check_tasks.scan_repo(warn_repo)

    assert quota_meta.is_human_action_required is True
    assert any("5H=12.0%" in b["reason"] for b in quota_meta.action_blockers)
    assert blocker_meta.is_human_action_required is True
    assert any("unavailable" in b["reason"] for b in blocker_meta.action_blockers)
    assert halt_meta.is_human_action_required is True
    assert any("FIX_PLAN_ESCALATE" in b["reason"] for b in halt_meta.action_blockers)
    assert warn_meta.is_human_action_required is False
    assert warn_meta.action_blockers == []
    assert any("quota_unknown" in n for n in warn_meta.notices)
    assert not any("quota_unknown" in n for n in halt_meta.notices)


def test_fpg_hp_07_memory_role_assistant_maps_to_architect(tmp_path: Path) -> None:
    """[FPG-HP-07] The legacy memory role assistant is reported as architect."""
    repo = _init_repo(tmp_path / "demo_repo")
    (repo / ".devtool").mkdir(parents=True, exist_ok=True)
    (repo / ".devtool" / "assistant_state.md").write_text(
        "# Active Epic: demo_epic\n- Role: assistant | Updated: 2026-11-17\n",
        encoding="utf-8",
    )
    assert check_tasks.extract_two_tier_memory(repo).assistant_state_role == "architect"

    (repo / ".devtool" / "assistant_state.md").write_text(
        "# Active Epic: demo_epic\n- Role: programmer | Updated: 2026-11-17\n",
        encoding="utf-8",
    )
    assert (
        check_tasks.extract_two_tier_memory(repo).assistant_state_role == "programmer"
    )


class _ViReadSpy:
    """Records every open() of a `.vi.md` path through `open` and `Path.open`."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.paths: list[str] = []
        real_builtin_open = builtins.open
        real_path_open = Path.open
        spy = self

        def _note(target: Any) -> None:
            with contextlib.suppress(TypeError):
                text = os.fspath(target)
                if str(text).endswith(".vi.md"):
                    spy.paths.append(str(text))

        def _open(file: Any, *args: Any, **kwargs: Any) -> Any:
            _note(file)
            return real_builtin_open(file, *args, **kwargs)

        def _path_open(self: Path, *args: Any, **kwargs: Any) -> Any:
            _note(self)
            return real_path_open(self, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", _open)
        monkeypatch.setattr(Path, "open", _path_open)


def test_fpg_hp_07_dashboard_documents_resolve_english_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[FPG-HP-07] Harvest, PIC resolution and PIC assignment never open a `.vi.md` file."""
    workspace = tmp_path / "workspace"
    repo = _init_repo(workspace / "demo_repo")
    epic_dir = repo / ".devtool" / "epic" / "demo_epic"
    epic_dir.mkdir(parents=True, exist_ok=True)
    hld = epic_dir / "demo_epic.md"
    hld.write_text(
        "# Epic: English Title\n\n- **PIC**: `alpha`\n- **Status**: In Progress\n",
        encoding="utf-8",
    )
    spec = epic_dir / "2026-11-17-demo-design.md"
    spec.write_text(
        "# Demo Design\n\n- **Epic Directory**: `demo_epic`\n", encoding="utf-8"
    )
    hld_vi = epic_dir / "demo_epic.vi.md"
    hld_vi.write_text(
        "# Epic: Tieu de\n\n- **PIC**: `beta`\n- **Trạng thái**: Hoàn tất\n",
        encoding="utf-8",
    )
    spec_vi = epic_dir / "2026-11-17-demo-design.vi.md"
    spec_vi.write_text("# Ban thiet ke\n\n- **PIC**: `beta`\n", encoding="utf-8")
    (epic_dir / "bdd_scenarios.vi.md").write_text("# BDD vi\n", encoding="utf-8")
    vi_before = {p: p.read_bytes() for p in (hld_vi, spec_vi)}

    spy = _ViReadSpy(monkeypatch)
    hld_vi.read_text(encoding="utf-8")
    assert spy.paths == [str(hld_vi)], "the spy must record a deliberate .vi.md read"
    spy.paths.clear()

    summary = check_tasks.harvest_epics_overview(repo)
    meta = check_tasks.scan_repo(repo)
    pic = check_tasks.extract_epic_pic(repo, "demo_epic")
    status = check_tasks.extract_epic_hld_status(epic_dir, "demo_epic")
    result = tasks_server.assign_epic_pic(workspace, "demo_repo", "demo_epic", "gamma")

    assert spy.paths == []
    assert summary.epics[0]["title"] == "English Title"
    assert summary.epics[0]["status"] == "in_progress"
    assert meta.account_id == "alpha"
    assert pic == "alpha"
    assert status == "in_progress"
    assert result["status"] == "ok"
    assert result.get("warnings") == []
    assert "`gamma`" in hld.read_text(encoding="utf-8")
    assert "`gamma`" in spec.read_text(encoding="utf-8")
    assert all(p.read_bytes() == data for p, data in vi_before.items())
    assert not any(".vi.md" in f for f in result["updated_files"])


def test_fpg_hp_07_hld_status_ignores_vietnamese_label_and_vi_files(
    tmp_path: Path,
) -> None:
    """[FPG-HP-07] The HLD status comes from English files with the English label only."""
    epic_dir = tmp_path / "epic_a"
    epic_dir.mkdir()
    (epic_dir / "epic_a.vi.md").write_text("- **Status**: Done\n", encoding="utf-8")
    assert check_tasks.extract_epic_hld_status(epic_dir, "epic_a") is None

    (epic_dir / "epic_a.md").write_text(
        "- **Trạng thái**: Hoàn tất\n", encoding="utf-8"
    )
    assert check_tasks.extract_epic_hld_status(epic_dir, "epic_a") is None

    (epic_dir / "epic_a.md").write_text("- **Status**: Done\n", encoding="utf-8")
    assert check_tasks.extract_epic_hld_status(epic_dir, "epic_a") == "done"

    (epic_dir / "epic_a.md").unlink()
    (epic_dir / "epic_a.en.md").write_text(
        "- **Status**: In Progress\n", encoding="utf-8"
    )
    assert check_tasks.extract_epic_hld_status(epic_dir, "epic_a") == "in_progress"


class TestFpgDashboardSync_Integration:
    """Integration runner for the dashboard scenarios that scan real state files."""

    def test_fpg_hp_07_payload_carries_persona_bindings_checkpoint_and_low_quota(
        self, tmp_path: Path, _isolated_host_env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[FPG-HP-07] [Tier C - Integration] The payload carries persona bindings, the checkpoint and low-quota state."""
        workspace = tmp_path / "workspace"
        repo = _init_repo(workspace / "demo_repo")
        _write_json(
            repo / ".agents" / "config" / "personas.json",
            {"schema_version": 1, "active_preset": "gemini-saver"},
        )
        expires = _utc(timedelta(hours=3))
        _write_json(
            _d3nexus(_isolated_host_env) / "personas.json",
            {
                "schema_version": 1,
                "low_quota": {"alpha": {"enabled": True, "expires_at": expires}},
            },
        )
        monkeypatch.setenv("AGY_PROFILE", "alpha")
        _seed_checkpoint(repo, "demo_epic")

        meta = check_tasks.scan_repo(repo)

        assert meta.persona_config_error is None
        assert [b["persona"] for b in meta.persona_bindings] == [
            "ai_architect_reviewer",
            "orchestrator",
            "programmer",
        ]
        orch = next(b for b in meta.persona_bindings if b["persona"] == "orchestrator")
        assert orch["alias"] == "hydrogen"
        assert orch["cli"] == "agy"
        assert orch["model_id"] == "gemini-4-hydrogen-medium"
        assert orch["effort"] == "medium"
        assert orch["fallback_alias"] == "claude-sonnet"
        assert orch["sources"]["model"] == "project"
        assert meta.checkpoint is not None
        assert meta.checkpoint["event"] == "wave_merged"
        assert meta.checkpoint["next_step"] == "start wave 3"
        assert meta.low_quota is not None
        assert meta.low_quota["enabled"] is True
        assert meta.low_quota["expires_at"] == expires

        with (
            _running_server(workspace, tmp_path / "tasks_server.pid") as port,
            (
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/tasks", timeout=10)
            ) as resp,
        ):
            payload = json.loads(resp.read().decode("utf-8"))
        served = next(r for r in payload["repos"] if r["name"] == "demo_repo")
        assert len(served["persona_bindings"]) == 3
        for entry in served["persona_bindings"]:
            for key in ("alias", "model_id", "effort", "sources"):
                assert key in entry
        assert served["checkpoint"]["event"] == "wave_merged"
        assert served["checkpoint"]["next_step"] == "start wave 3"
        assert served["low_quota"]["enabled"] is True
        assert served["low_quota"]["expires_at"] == expires

        html = DASHBOARD_HTML.read_text(encoding="utf-8")
        for hook in (
            "renderPersonaBindings",
            "renderCheckpointStatus",
            "renderAgyProfiles",
        ):
            assert f"function {hook}(" in html
        assert "persona-bindings-" in html
        assert "checkpoint-status-" in html
        assert "Tri-Role" not in html

    @pytest.mark.parametrize(
        ("scenario", "expect_checkpoint", "expect_low_quota"),
        [
            ("absent", False, False),
            ("invalid", False, False),
            ("expired_low_quota", True, False),
        ],
    )
    def test_fpg_hp_07_absent_and_invalid_inputs_leave_empty_fields(
        self,
        tmp_path: Path,
        _isolated_host_env: Path,
        monkeypatch: pytest.MonkeyPatch,
        scenario: str,
        expect_checkpoint: bool,
        expect_low_quota: bool,
    ) -> None:
        """[FPG-HP-07] Absent or invalid checkpoint and low-quota inputs leave the new fields empty."""
        repo = _init_repo(tmp_path / "demo_repo")
        monkeypatch.setenv("AGY_PROFILE", "alpha")
        if scenario == "invalid":
            _seed_checkpoint(repo, "demo_epic")
            safe = _state_envelope._sanitize_epic_slug("demo_epic")
            hb_path = repo / ".devtool" / "state" / f"{safe}.heartbeat.json"
            hb = json.loads(hb_path.read_text(encoding="utf-8"))
            hb["checkpoint"] = "not-a-mapping"
            hb_path.write_text(json.dumps(hb), encoding="utf-8")
        if scenario == "expired_low_quota":
            _seed_checkpoint(repo, "demo_epic")
            _write_json(
                _d3nexus(_isolated_host_env) / "personas.json",
                {
                    "schema_version": 1,
                    "low_quota": {
                        "alpha": {
                            "enabled": True,
                            "expires_at": _utc(timedelta(hours=-1)),
                        }
                    },
                },
            )

        meta = check_tasks.scan_repo(repo)

        assert (meta.checkpoint is not None) is expect_checkpoint
        assert (meta.low_quota is not None) is expect_low_quota
        assert len(meta.persona_bindings) == 3
        assert {b["sources"]["model"] for b in meta.persona_bindings} == {"kit"}
        assert meta.agy_pool is None or meta.agy_pool["state"] == "empty"
        assert meta.agy_profiles == []
        assert meta.is_human_action_required is False

    @pytest.mark.parametrize(
        "token",
        ["MODEL_UNAVAILABLE", "QUOTA_LOW", "LOW_QUOTA_STOP", "FIX_PLAN_ESCALATE"],
    )
    def test_fpg_st_04_each_heartbeat_halt_reason_is_human_action(
        self, tmp_path: Path, token: str
    ) -> None:
        """[FPG-ST-04] Every recognised heartbeat halt reason sets human action and an alert."""
        repo = _init_repo(tmp_path / "halt_repo")
        _seed_checkpoint(repo, "halt_epic")
        _set_heartbeat_halt(repo, "halt_epic", token)

        meta = check_tasks.scan_repo(repo)

        assert meta.is_human_action_required is True
        matching = [b for b in meta.action_blockers if token in b["reason"]]
        assert len(matching) == 1
        assert matching[0]["epic"] == "halt_epic"

    @pytest.mark.parametrize("token", ["LOW_QUOTA_STOP", "MODEL_UNAVAILABLE"])
    def test_fpg_st_04_state_text_halt_reason_is_human_action(
        self, tmp_path: Path, token: str
    ) -> None:
        """[FPG-ST-04] A halt reason recorded in the epic state text sets human action."""
        repo = _init_repo(tmp_path / "state_repo")
        _seed_checkpoint(repo, "state_epic")
        state_file = repo / ".devtool" / "state" / "state_epic.md"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(
            f"# Active Epic: state_epic\n\n## Next Immediate Step:\n- halt_reason: {token}\n",
            encoding="utf-8",
        )

        meta = check_tasks.scan_repo(repo)

        assert meta.is_human_action_required is True
        assert any(token in b["reason"] for b in meta.action_blockers)

    @pytest.mark.parametrize(
        "value", ["fix_plan_escalate", "QUOTA_LOW_SOON", "", None, 7]
    )
    def test_fpg_st_04_halt_matching_is_case_sensitive_and_exact(
        self, tmp_path: Path, value: object
    ) -> None:
        """[FPG-ST-04] Lowercase, partial, empty and non-string halt values are ignored."""
        repo = _init_repo(tmp_path / "halt_repo")
        _seed_checkpoint(repo, "halt_epic")
        safe = _state_envelope._sanitize_epic_slug("halt_epic")
        hb_path = repo / ".devtool" / "state" / f"{safe}.heartbeat.json"
        hb = json.loads(hb_path.read_text(encoding="utf-8"))
        hb["halt_reason"] = value
        hb_path.write_text(json.dumps(hb), encoding="utf-8")

        meta = check_tasks.scan_repo(repo)

        assert meta.is_human_action_required is False
        assert meta.action_blockers == []

    def test_fpg_st_04_pending_quota_decision_for_a_sibling_epic_still_alerts(
        self,
        tmp_path: Path,
    ) -> None:
        """[FPG-ST-04] A quota decision on an epic that is not the active one still alerts the repository."""
        repo = _init_repo(tmp_path / "multi_repo")
        _seed_checkpoint(repo, "main_epic")
        _seed_epic_with_decision(repo, "side_epic", "quota", "programmer agy 5H=3.0%")

        meta = check_tasks.scan_repo(repo)

        assert meta.is_human_action_required is True
        assert any("5H=3.0%" in b["reason"] for b in meta.action_blockers)


def test_checkpoint_wave_zero_converts_to_string_before_escape_html() -> None:
    """S7: buildCheckpointLineHtml must convert checkpoint.wave to string before calling escapeHtml (0 is falsy)."""
    html = DASHBOARD_HTML.read_text(encoding="utf-8")
    start = html.index("function buildCheckpointLineHtml(")
    end = html.index("function buildCheckpointStatusHtml(", start)
    fn_source = html[start:end]
    assert "escapeHtml(String(checkpoint.wave))" in fn_source
    assert "escapeHtml(checkpoint.wave)" not in fn_source


@pytest.mark.parametrize(
    ("status_label", "source_kind"),
    [
        ("Done", "heartbeat"),
        ("Done", "state"),
        ("Abandoned", "heartbeat"),
        ("Abandoned", "state"),
    ],
)
def test_finished_or_abandoned_epic_halt_tokens_do_not_set_human_action(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status_label: str,
    source_kind: str,
) -> None:
    """S8: Halt tokens for completed or abandoned epics must be skipped by _collect_orchestrator_signals."""
    repo = _init_repo(tmp_path / "closed_halt_repo")
    epic = "closed_epic"
    epic_dir = repo / ".devtool" / "epic" / epic
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / f"{epic}.md").write_text(
        f"# Epic: Closed\n\n- **Status**: {status_label}\n",
        encoding="utf-8",
    )
    if source_kind == "heartbeat":
        _set_heartbeat_halt(repo, epic, "FIX_PLAN_ESCALATE")
    else:
        state_file = repo / ".devtool" / "state" / f"{epic}.md"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(
            f"# Active Epic: {epic}\n\n## Next Immediate Step:\n- halt_reason: QUOTA_LOW\n",
            encoding="utf-8",
        )

    completed = check_tasks.get_completed_epic_slugs(repo)
    abandoned = check_tasks.get_abandoned_epic_slugs(repo)
    closed = completed | abandoned
    assert epic in closed
    hb = check_tasks._read_epic_heartbeat(repo, epic)

    signals = check_tasks._collect_orchestrator_signals(
        repo,
        epic,
        None,
        hb,
        decisions_snapshot={},
        stage_name="Idle",
        seen_blockers=set(),
        closed_slugs=closed,
    )
    assert [b for b in signals.blockers if b.get("kind") == "halt"] == []

    monkeypatch.setattr(check_tasks, "resolve_active_epic", lambda _r: epic)
    meta = check_tasks.scan_repo(repo)
    assert meta.is_human_action_required is False
    assert [b for b in meta.action_blockers if b.get("kind") == "halt"] == []
