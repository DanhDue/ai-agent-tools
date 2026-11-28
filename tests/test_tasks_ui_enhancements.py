"""Tests for check-tasks UI & backend enhancements:
1. Epics Overview wrap-content width, top alignment, and Approval Blockers overflow containment.
2. Execution Logs permanently collapsed with Copy All Logs button.
3. Agy Profile Pool quota progress bars in the middle and current task column on the far right.
4. Tracked projects backend config/APIs and long-click header bar edit mode (Add Project + Close/Undo).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import http.server
import json
from pathlib import Path
import socketserver
import subprocess
import sys
import threading
import time
from typing import Any
from unittest.mock import patch
import urllib.error
import urllib.request

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
DASHBOARD_HTML = (
    REPO_ROOT
    / "skills"
    / "check-tasks"
    / "resources"
    / "dashboard"
    / "tasks_dashboard.html"
)
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_tasks  # noqa: E402
import tasks_server  # noqa: E402
from tests.test_rsdh_tasks_dashboard_ui import (  # noqa: E402
    _NODE_CDP_HELPER,
    _resolve_chrome_binary,
    _run_node_script,
)


def _init_git_repo(repo_dir: Path, *, theme_color: str | None = None) -> Path:
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.local"], cwd=repo_dir, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True
    )
    (repo_dir / "README.md").write_text(f"# {repo_dir.name}\n", encoding="utf-8")
    if theme_color:
        vscode = repo_dir / ".vscode"
        vscode.mkdir(parents=True, exist_ok=True)
        (vscode / "settings.json").write_text(
            json.dumps(
                {
                    "workbench.colorCustomizations": {
                        "titleBar.activeBackground": theme_color,
                    }
                }
            ),
            encoding="utf-8",
        )
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    return repo_dir


def _http_json(
    url: str, method: str = "GET", payload: dict[str, Any] | None = None
) -> tuple[int, dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


class TestTrackedProjectsBackend:
    """Backend persistence and REST API tests for tracked project management."""

    def test_add_remove_undo_and_external_repo_resolution(self, tmp_path: Path) -> None:
        ws = tmp_path / "workspace"
        external_root = tmp_path / "external_projects"
        _init_git_repo(ws / "D3Nexus", theme_color="#065f46")
        _init_git_repo(ws / "ai-agent-tools", theme_color="#b45309")
        _init_git_repo(ws / "untracked-sibling")
        ext_repo = _init_git_repo(external_root / "wallet-app", theme_color="#7c3aed")
        epic_dir = ext_repo / ".devtool" / "epic" / "wallet_epic"
        epic_dir.mkdir(parents=True, exist_ok=True)
        (epic_dir / "wallet_epic.md").write_text(
            "# Epic: Wallet\n\n- **PIC**: `danhdue`\n- **Status**: In Progress\n",
            encoding="utf-8",
        )
        non_git = tmp_path / "plain_dir"
        non_git.mkdir()

        cfg_path = tmp_path / "tracked_projects.json"
        port = tasks_server.find_available_port(19850)
        server = tasks_server.TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=ws,
            pid_file=tmp_path / "srv.pid",
            projects_config_path=cfg_path,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.1)
        base = f"http://127.0.0.1:{port}"

        try:
            # 1. GET /api/projects before config exists lists seeded canonical repos + untracked suggestion
            code, proj_data = _http_json(f"{base}/api/projects")
            assert code == 200
            assert proj_data["config_exists"] is False
            assert [p["name"] for p in proj_data["projects"]] == [
                "D3Nexus",
                "ai-agent-tools",
            ]
            assert [s["name"] for s in proj_data["suggestions"]] == [
                "untracked-sibling"
            ]

            # 2. Validation rejects non-git folder and missing folder
            code_bad, err_bad = _http_json(
                f"{base}/api/projects/add",
                method="POST",
                payload={"path": str(non_git)},
            )
            assert code_bad == 400
            assert "not a Git repository" in err_bad["error"]

            code_missing, _ = _http_json(
                f"{base}/api/projects/add",
                method="POST",
                payload={"path": str(tmp_path / "missing")},
            )
            assert code_missing == 400

            # 3. Add external repo outside workspace_root -> persisted and scanned by /api/tasks
            code_add, added = _http_json(
                f"{base}/api/projects/add",
                method="POST",
                payload={"path": str(ext_repo)},
            )
            assert code_add == 200
            assert added["project"]["name"] == "wallet-app"
            assert cfg_path.is_file()

            # Duplicate add returns 409
            code_dup, _ = _http_json(
                f"{base}/api/projects/add",
                method="POST",
                payload={"path": str(ext_repo)},
            )
            assert code_dup == 409

            code_tasks, tasks_data = _http_json(f"{base}/api/tasks")
            assert code_tasks == 200
            assert [p["name"] for p in tasks_data["tracked_projects"]] == [
                "D3Nexus",
                "ai-agent-tools",
                "wallet-app",
            ]
            repo_names = [r["name"] for r in tasks_data["repos"]]
            assert repo_names == ["D3Nexus", "ai-agent-tools", "wallet-app"]

            # External tracked repo resolves cleanly for /api/epic/history and /api/epic/pic
            code_hist, hist = _http_json(
                f"{base}/api/epic/history?repo=wallet-app&epic=wallet_epic"
            )
            assert code_hist == 200
            assert hist["success"] is True
            assert hist["epic"]["slug"] == "wallet_epic"
            assert hist["reviews"]["principal"]["repo"] == "wallet-app"

            code_pic, pic_res = _http_json(
                f"{base}/api/epic/pic",
                method="POST",
                payload={"repo": "wallet-app", "epic": "wallet_epic", "pic": "tess"},
            )
            assert code_pic == 200
            assert pic_res["status"] == "ok"

            # 4. Remove tracked project does NOT delete folder on disk, and Undo restores original index
            code_rm, rm_res = _http_json(
                f"{base}/api/projects/remove",
                method="POST",
                payload={"name": "ai-agent-tools"},
            )
            assert code_rm == 200
            assert rm_res["removed"]["name"] == "ai-agent-tools"
            assert rm_res["removed"]["index"] == 1
            assert (ws / "ai-agent-tools").is_dir()
            assert [p["name"] for p in rm_res["projects"]] == ["D3Nexus", "wallet-app"]

            code_undo, undo_res = _http_json(
                f"{base}/api/projects/add",
                method="POST",
                payload={
                    "path": str(ws / "ai-agent-tools"),
                    "index": rm_res["removed"]["index"],
                },
            )
            assert code_undo == 200
            assert [p["name"] for p in undo_res["projects"]] == [
                "D3Nexus",
                "ai-agent-tools",
                "wallet-app",
            ]
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_browse_endpoint_handles_ok_and_cancel(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        ws.mkdir()
        port = tasks_server.find_available_port(19880)
        server = tasks_server.TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=ws,
            pid_file=tmp_path / "browse.pid",
            projects_config_path=tmp_path / "cfg.json",
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.1)
        base = f"http://127.0.0.1:{port}"
        try:
            with patch.object(
                tasks_server,
                "pick_folder_macos",
                return_value={
                    "status": "ok",
                    "path": "/Users/testuser/AllProjects/demo",
                },
            ):
                code, res = _http_json(
                    f"{base}/api/projects/browse", method="POST", payload={}
                )
                assert code == 200
                assert res["status"] == "ok"
                assert res["path"] == "~/AllProjects/demo"

            with patch.object(
                tasks_server,
                "pick_folder_macos",
                return_value={"status": "cancelled"},
            ):
                code_c, res_c = _http_json(
                    f"{base}/api/projects/browse", method="POST", payload={}
                )
                assert code_c == 200
                assert res_c["status"] == "cancelled"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_orphan_server_probe_and_reclaim_on_port(self, tmp_path: Path) -> None:
        """Orphan check-tasks daemon without PID file is detected by port probe and reclaimed."""
        ws = tmp_path / "ws"
        ws.mkdir()
        port = tasks_server.find_available_port(19910)
        orphan_pid_file = tmp_path / "orphan.pid"
        server = tasks_server.TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=ws,
            pid_file=orphan_pid_file,
            projects_config_path=tmp_path / "cfg.json",
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.1)
        try:
            # Simulate lost PID file while server is still squatting on port
            orphan_pid_file.unlink(missing_ok=True)
            info = tasks_server.probe_running_server_on_port(port)
            assert info is not None
            assert info["status"] == "running"
            assert info["port"] == port

            # Stale fingerprint detection works against status payload
            assert (
                tasks_server._is_status_payload_stale(
                    info, ws, expected_fingerprint="different_fp"
                )
                is True
            )
            assert (
                tasks_server._is_status_payload_stale(
                    info, ws, expected_fingerprint=info["code_fingerprint"]
                )
                is False
            )

            # Reclaiming stops the server cleanly via /api/shutdown
            with patch.object(tasks_server, "_terminate_pid", return_value=True):
                tasks_server.stop_server_on_port(port)
            thread.join(timeout=3)
            assert tasks_server.probe_running_server_on_port(port) is None
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_pick_folder_macos_activates_dialog_foreground(
        self, tmp_path: Path
    ) -> None:
        """pick_folder_macos centers native NSOpenPanel over browser windowBounds via JXA."""

        class _FakeProc:
            returncode = 0

            def communicate(self, timeout: float | None = None) -> tuple[str, str]:
                return ("/Users/tester/AllProjects/app/\n", "")

            def poll(self) -> int:
                return 0

        bounds = {"x": 120, "y": 80, "width": 1200, "height": 900}
        with (
            patch.object(sys, "platform", "darwin"),
            patch.object(
                tasks_server.subprocess, "Popen", return_value=_FakeProc()
            ) as popen_mock,
        ):
            res = tasks_server.pick_folder_macos(
                "Pick repo", default_dir=tmp_path, window_bounds=bounds
            )
        assert res == {"status": "ok", "path": "/Users/tester/AllProjects/app"}
        argv = popen_mock.call_args[0][0]
        assert argv[:4] == ["osascript", "-l", "JavaScript", "-e"]
        jxa = argv[4]
        assert "NSOpenPanel" in jxa
        assert "activateIgnoringOtherApps(true)" in jxa
        assert "panel.orderFrontRegardless()" not in jxa
        assert "panel.orderFrontRegardless;" in jxa
        assert "panel.center;" in jxa
        assert "panel.setFrameOrigin(" in jxa
        assert '"width": 1200' in jxa
        assert str(tmp_path.resolve()) in jxa
        if sys.platform == "darwin":
            # Execute the real JXA ObjC setup lines before runModal so zero-arg
            # selector call regressions and browser-window centering math are verified live.
            setup_jxa = jxa.split("const resp = Number(panel.runModal);", 1)[0]
            probe = subprocess.run(
                [
                    "osascript",
                    "-l",
                    "JavaScript",
                    "-e",
                    (
                        f"{setup_jxa}\n"
                        "const f = panel.frame;\n"
                        "const pf0 = screens.objectAtIndex(0).frame;\n"
                        "panel.close;\n"
                        "JSON.stringify({"
                        "px: f.origin.x, py: f.origin.y, pw: f.size.width, ph: f.size.height, "
                        "pTop: pf0.origin.y + pf0.size.height, "
                        "tx: targetFrame ? targetFrame.origin.x : 0, "
                        "ty: targetFrame ? targetFrame.origin.y : 0, "
                        "tw: targetFrame ? targetFrame.size.width : 0, "
                        "th: targetFrame ? targetFrame.size.height : 0"
                        "});\n"
                    ),
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            assert probe.returncode == 0, probe.stderr
            geom = json.loads(probe.stdout.strip())
            if geom["tw"] > 0 and geom["th"] > 0:
                anchor_x = bounds["x"] + bounds["width"] / 2
                anchor_y = geom["pTop"] - (bounds["y"] + bounds["height"] / 2)
                exp_x = round(anchor_x - geom["pw"] / 2)
                exp_y = round(anchor_y - geom["ph"] / 2)
                max_x = round(geom["tx"] + geom["tw"] - geom["pw"])
                max_y = round(geom["ty"] + geom["th"] - geom["ph"])
                if max_x >= geom["tx"]:
                    exp_x = max(round(geom["tx"]), min(exp_x, max_x))
                if max_y >= geom["ty"]:
                    exp_y = max(round(geom["ty"]), min(exp_y, max_y))
                assert abs(geom["px"] - exp_x) <= 2, geom
                assert abs(geom["py"] - exp_y) <= 2, geom

    def test_cancel_active_folder_picker_and_browse_cancel_endpoint(
        self, tmp_path: Path
    ) -> None:
        """POST /api/projects/browse/cancel terminates the live picker subprocess cleanly."""
        ws = tmp_path / "ws"
        ws.mkdir()
        _init_git_repo(ws / "repo_a")
        port = tasks_server.find_available_port(19920)
        server = tasks_server.TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=ws,
            pid_file=tmp_path / "browse_cancel.pid",
            projects_config_path=tmp_path / "projects.json",
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.1)
        base = f"http://127.0.0.1:{port}"
        orig_popen = subprocess.Popen
        spawned_event = threading.Event()
        browse_result: dict[str, Any] = {}

        def _fake_sleep_popen(*_args: Any, **_kwargs: Any) -> subprocess.Popen[str]:
            proc = orig_popen(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            spawned_event.set()
            return proc

        try:
            with (
                patch.object(sys, "platform", "darwin"),
                patch.object(
                    tasks_server.subprocess, "Popen", side_effect=_fake_sleep_popen
                ),
            ):

                def _call_browse() -> None:
                    code, body = _http_json(
                        f"{base}/api/projects/browse",
                        method="POST",
                        payload={
                            "windowBounds": {
                                "x": 100,
                                "y": 50,
                                "width": 1000,
                                "height": 700,
                            }
                        },
                    )
                    browse_result["code"] = code
                    browse_result["body"] = body

                browse_thread = threading.Thread(target=_call_browse, daemon=True)
                browse_thread.start()
                assert spawned_event.wait(timeout=3), "Picker subprocess did not start"
                # Wait briefly until tasks_server registers _ACTIVE_FOLDER_PICKER_PROC
                deadline = time.monotonic() + 2.0
                while (
                    tasks_server._ACTIVE_FOLDER_PICKER_PROC is None
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.02)
                assert tasks_server._ACTIVE_FOLDER_PICKER_PROC is not None

                cancel_code, cancel_body = _http_json(
                    f"{base}/api/projects/browse/cancel", method="POST", payload={}
                )
                assert cancel_code == 200
                assert cancel_body == {"status": "ok", "cancelled": True}

                browse_thread.join(timeout=3)
                assert not browse_thread.is_alive()
                assert browse_result["code"] == 200
                assert browse_result["body"] == {"status": "cancelled"}
                assert tasks_server._ACTIVE_FOLDER_PICKER_PROC is None

                # Calling cancel when nothing is open is a clean no-op
                noop_code, noop_body = _http_json(
                    f"{base}/api/projects/browse/cancel", method="POST", payload={}
                )
                assert noop_code == 200
                assert noop_body == {"status": "ok", "cancelled": False}
        finally:
            tasks_server.cancel_active_folder_picker()
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_scan_repo_caches_hld_status_and_overview_per_scan(
        self, tmp_path: Path
    ) -> None:
        """Per-scan cache avoids O(E^2) repeated HLD reads across multiple epics."""
        repo = _init_git_repo(tmp_path / "many_epics")
        for idx in range(6):
            ep_dir = repo / ".devtool" / "epic" / f"epic_{idx:02d}"
            ep_dir.mkdir(parents=True, exist_ok=True)
            status = "In Progress" if idx < 3 else "Done"
            (ep_dir / f"epic_{idx:02d}.md").write_text(
                f"# Epic {idx}\n\n- **Status**: {status}\n",
                encoding="utf-8",
            )

        hld_calls = 0
        orig_hld = check_tasks.extract_epic_hld_status

        def counting_hld(epic_dir: Path, slug: str) -> str | None:
            nonlocal hld_calls
            cache = getattr(check_tasks._SCAN_CTX, "cache", None)
            if not (
                isinstance(cache, dict) and ("hld_status", str(epic_dir), slug) in cache
            ):
                hld_calls += 1
            return orig_hld(epic_dir, slug)

        with patch.object(
            check_tasks, "extract_epic_hld_status", side_effect=counting_hld
        ):
            meta = check_tasks.scan_repo(repo)
        assert meta.epics_summary is not None
        assert meta.epics_summary.total == 6
        assert hld_calls == 6, f"Expected O(E)=6 HLD disk scans, got {hld_calls}"

    def test_coalesced_tasks_requests_share_single_inflight_harvest(
        self, tmp_path: Path
    ) -> None:
        """Concurrent GET /api/tasks requests coalesce into one in-flight harvest call."""
        ws = tmp_path / "ws"
        ws.mkdir()
        port = tasks_server.find_available_port(19940)
        server = tasks_server.TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=ws,
            pid_file=tmp_path / "coalesce.pid",
            projects_config_path=tmp_path / "cfg.json",
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.1)

        harvest_calls = 0
        gate = threading.Event()
        started = threading.Event()
        real_harvest = tasks_server.harvest_dashboard_graph

        def slow_harvest(*args: Any, **kwargs: Any) -> Any:
            nonlocal harvest_calls
            harvest_calls += 1
            started.set()
            gate.wait(timeout=3)
            return real_harvest(*args, **kwargs)

        try:
            with patch.object(
                tasks_server, "harvest_dashboard_graph", side_effect=slow_harvest
            ):
                results: list[int] = []

                def worker() -> None:
                    code, _ = _http_json(f"http://127.0.0.1:{port}/api/tasks")
                    results.append(code)

                t1 = threading.Thread(target=worker)
                t2 = threading.Thread(target=worker)
                t1.start()
                assert started.wait(timeout=3)
                t2.start()
                time.sleep(0.15)
                gate.set()
                t1.join(timeout=5)
                t2.join(timeout=5)

            assert results == [200, 200]
            assert harvest_calls == 1
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_focus_repo_header_scans_only_selected_repo_and_falls_back(
        self, tmp_path: Path
    ) -> None:
        """GET /api/tasks with X-Focus-Repo scans only the saved tab for fast cold start."""
        ws = tmp_path / "ws"
        _init_git_repo(ws / "D3Nexus")
        _init_git_repo(ws / "ai-agent-tools")
        port = tasks_server.find_available_port(19960)
        server = tasks_server.TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=ws,
            pid_file=tmp_path / "focus.pid",
            projects_config_path=tmp_path / "cfg.json",
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.1)
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/tasks",
                headers={"X-Focus-Repo": "ai-agent-tools"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                assert resp.status == 200
                data = json.loads(resp.read().decode("utf-8"))
            assert data["partial"] is True
            assert data["focus_repo"] == "ai-agent-tools"
            assert [r["name"] for r in data["repos"]] == ["ai-agent-tools"]

            # Unknown saved tab gracefully falls back to full multi-repo scan
            req_bad = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/tasks",
                headers={"X-Focus-Repo": "deleted-repo"},
            )
            with urllib.request.urlopen(req_bad, timeout=5) as resp_bad:
                assert resp_bad.status == 200
                full_data = json.loads(resp_bad.read().decode("utf-8"))
            assert full_data.get("partial") is not True
            assert sorted(r["name"] for r in full_data["repos"]) == [
                "D3Nexus",
                "ai-agent-tools",
            ]
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_agy_pool_priority_endpoint_updates_and_validates(
        self, tmp_path: Path
    ) -> None:
        """POST /api/agy-pool/priority updates priority under lock even with live leases."""
        ws = tmp_path / "ws"
        ws.mkdir()
        fake_home = tmp_path / "home"
        d3 = fake_home / ".d3nexus"
        d3.mkdir(parents=True, exist_ok=True)
        pool_path = d3 / "agy_profiles.json"
        pool_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "allow_concurrent_ag_run": True,
                    "pool": [
                        {
                            "profile": "khangatuaon248",
                            "priority": 1,
                            "max_concurrent": 6,
                        },
                        {"profile": "hau", "priority": 2, "max_concurrent": 2},
                        {"profile": "duedd", "priority": 3, "max_concurrent": 2},
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        leases_path = d3 / "agy_pool_leases.json"
        leases_doc = {
            "schema_version": 1,
            "profiles": {
                "khangatuaon248": {
                    "leases": [
                        {
                            "owner_id": "owner-live-1",
                            "pid": 999999,
                            "host": "test-host",
                            "launch": "direct",
                            "epic": "ep1",
                            "task": "task_01",
                            "slot": 1,
                            "role": "orchestrator",
                            "repo": "ai-agent-tools",
                            "acquired_at": "2026-11-28T00:00:00Z",
                            "heartbeat_at": "2026-11-28T00:00:00Z",
                        }
                    ],
                    "exhausted_until": None,
                    "exhausted_checked_at": None,
                    "exhausted_reason": None,
                    "quota": None,
                }
            },
        }
        leases_path.write_text(json.dumps(leases_doc, indent=2), encoding="utf-8")

        port = tasks_server.find_available_port(19975)
        server = tasks_server.TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=ws,
            pid_file=tmp_path / "prio.pid",
            projects_config_path=tmp_path / "cfg.json",
            agy_pool_real_home=fake_home,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.1)
        base = f"http://127.0.0.1:{port}"
        try:
            # Promote duedd from 3 -> 1 and move leased khangatuaon248 from 1 -> 4
            code_ok, res_ok = _http_json(
                f"{base}/api/agy-pool/priority",
                method="POST",
                payload={"profile": "duedd", "priority": 1},
            )
            assert code_ok == 200
            assert res_ok["status"] == "ok"
            assert res_ok["profile"] == "duedd"
            assert res_ok["priority"] == 1
            assert [p["profile"] for p in res_ok["pool"]] == [
                "duedd",
                "khangatuaon248",
                "hau",
            ]

            # Update max_concurrent via /api/agy-pool/settings including 0 (disabled) and 6
            code_zero, res_zero = _http_json(
                f"{base}/api/agy-pool/settings",
                method="POST",
                payload={"profile": "hau", "max_concurrent": 0},
            )
            assert code_zero == 200
            assert res_zero["status"] == "ok"
            assert res_zero["max_concurrent"] == 0

            code_both, res_both = _http_json(
                f"{base}/api/agy-pool/settings",
                method="POST",
                payload={
                    "profile": "khangatuaon248",
                    "priority": 4,
                    "max_concurrent": 5,
                },
            )
            assert code_both == 200
            assert res_both["priority"] == 4
            assert res_both["max_concurrent"] == 5
            assert [p["profile"] for p in res_both["pool"]] == [
                "duedd",
                "hau",
                "khangatuaon248",
            ]
            # Persisted on disk and live leases untouched
            saved = json.loads(pool_path.read_text(encoding="utf-8"))
            assert [
                (p["profile"], p["priority"], p["max_concurrent"])
                for p in saved["pool"]
            ] == [
                ("duedd", 1, 2),
                ("hau", 2, 0),
                ("khangatuaon248", 4, 5),
            ]
            assert json.loads(leases_path.read_text(encoding="utf-8")) == leases_doc

            # Invalid payloads rejected cleanly
            for endpoint, bad_payload, expected_code in (
                ("/api/agy-pool/priority", {"profile": "duedd"}, 400),
                ("/api/agy-pool/priority", {"profile": "duedd", "priority": 0}, 400),
                ("/api/agy-pool/priority", {"profile": "duedd", "priority": -2}, 400),
                ("/api/agy-pool/priority", {"profile": "duedd", "priority": True}, 400),
                (
                    "/api/agy-pool/priority",
                    {"profile": "duedd", "priority": "abc"},
                    400,
                ),
                (
                    "/api/agy-pool/priority",
                    {"profile": "nonexistent", "priority": 2},
                    404,
                ),
                ("/api/agy-pool/settings", {"profile": "duedd"}, 400),
                (
                    "/api/agy-pool/settings",
                    {"profile": "duedd", "max_concurrent": -1},
                    400,
                ),
                (
                    "/api/agy-pool/settings",
                    {"profile": "duedd", "max_concurrent": False},
                    400,
                ),
                (
                    "/api/agy-pool/settings",
                    {"profile": "duedd", "max_concurrent": "bad"},
                    400,
                ),
                (
                    "/api/agy-pool/settings",
                    {"profile": "ghost", "max_concurrent": 0},
                    404,
                ),
            ):
                code_err, res_err = _http_json(
                    f"{base}{endpoint}",
                    method="POST",
                    payload=bad_payload,
                )
                assert code_err == expected_code, (
                    endpoint,
                    bad_payload,
                    code_err,
                    res_err,
                )
                assert res_err["status"] == "error"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def test_tasks_dashboard_chrome_cdp_enhancements_e2e(tmp_path: Path) -> None:
    """Real Headless Chrome CDP E2E covering all 5 tasks dashboard UI enhancements."""
    chrome_bin = _resolve_chrome_binary()
    if not chrome_bin:
        pytest.skip("Headless Chrome not available")

    ws = tmp_path / "workspace"
    ext_root = tmp_path / "external"
    _init_git_repo(ws / "D3Nexus", theme_color="#065f46")
    _init_git_repo(ws / "ai-agent-tools", theme_color="#b45309")
    _init_git_repo(ws / "untracked-demo", theme_color="#0ea5e9")
    ext_repo = _init_git_repo(ext_root / "custom-mobile", theme_color="#7c3aed")
    cfg_path = tmp_path / "projects.json"

    future_5h = (datetime.now(timezone.utc) + timedelta(hours=3, minutes=20)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    future_wk = (datetime.now(timezone.utc) + timedelta(days=5, hours=4)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    long_unbroken_notice = (
        "agy profile huynhminhtien0510 is in use by "
        "quality_governance_hardening/task_05_remediate_security_theme_tokens_and_code_health_with_extremely_long_unbroken_identifier_segment/slot 1"
    )
    events = [
        {
            "ts": f"2026-11-27T17:{i:02d}:00Z",
            "stage": "Stage 3 Phase 2 (TDD)",
            "sub_step": "bdd_plan",
            "message": f"Execution event line #{i + 1}",
        }
        for i in range(12)
    ]

    fixture_pool_settings: dict[str, dict[str, int]] = {
        "khangatuaon248": {"priority": 1, "max_concurrent": 6},
        "huynhminhtien0510": {"priority": 2, "max_concurrent": 2},
        "hau": {"priority": 3, "max_concurrent": 2},
    }
    pool_updates_received: list[dict[str, Any]] = []
    browse_payloads: list[dict[str, Any]] = []
    browse_cancel_event = threading.Event()
    browse_cancel_count = [0]

    def build_synthetic_repos() -> tuple[
        list[dict[str, Any]], list[dict[str, str]] | None
    ]:
        tracked = check_tasks.load_tracked_projects(ws, cfg_path)
        effective = (
            tracked
            if tracked is not None
            else check_tasks.build_initial_tracked_projects(ws)
        )
        raw_agy_profiles = [
            {
                "profile": "khangatuaon248",
                "priority": fixture_pool_settings["khangatuaon248"]["priority"],
                "max_concurrent": fixture_pool_settings["khangatuaon248"][
                    "max_concurrent"
                ],
                "is_exhausted": False,
                "leased_by": [
                    {
                        "epic": "align_studio_post_editing_realign",
                        "task": "task_01_media_resolver",
                        "slot": 1,
                        "role": "orchestrator",
                        "repo": "align_studio-slot-1",
                    }
                ],
                "quota_5h": {"fraction": 0.783, "resetTime": future_5h},
                "quota_weekly": {"fraction": 0.92, "resetTime": future_wk},
            },
            {
                "profile": "huynhminhtien0510",
                "priority": fixture_pool_settings["huynhminhtien0510"]["priority"],
                "max_concurrent": fixture_pool_settings["huynhminhtien0510"][
                    "max_concurrent"
                ],
                "is_exhausted": False,
                "leased_by": [
                    {
                        "epic": "ios_quality_parity",
                        "task": "task_05_dual_floor",
                        "slot": 2,
                        "role": "orchestrator",
                        "repo": "ios_quality-slot-2",
                    }
                ],
                "quota_5h": {"fraction": 0.284, "resetTime": future_5h},
                "quota_weekly": {"fraction": 0.351, "resetTime": future_wk},
            },
            {
                "profile": "hau",
                "priority": fixture_pool_settings["hau"]["priority"],
                "max_concurrent": fixture_pool_settings["hau"]["max_concurrent"],
                "is_exhausted": True,
                "exhausted_reason": "weekly",
                "exhausted_until": future_wk,
                "leased_by": [],
                "quota_5h": {"fraction": 0.811, "resetTime": future_5h},
                "quota_weekly": {"fraction": 0.014, "resetTime": future_wk},
            },
        ]
        raw_agy_profiles.sort(key=lambda item: (int(item["priority"]), item["profile"]))
        repos: list[dict[str, Any]] = []
        for entry in effective:
            name = entry["name"]
            color = (
                "#065f46"
                if name == "D3Nexus"
                else ("#b45309" if name == "ai-agent-tools" else "#7c3aed")
            )
            repos.append(
                {
                    "name": name,
                    "path": entry["path"],
                    "theme_color": color,
                    "account_id": "danhdue",
                    "active_epic": "ui_polish_epic",
                    "active_stage": "Stage 3 Phase 2 (TDD)",
                    "prompt": "",
                    "is_human_action_required": False,
                    "notices": [long_unbroken_notice, long_unbroken_notice],
                    "worktrees": [],
                    "task_progress": {
                        "total_tasks": 4,
                        "done_tasks": 2,
                        "in_progress_tasks": 1,
                        "todo_tasks": 1,
                        "percentage": 50.0,
                        "tasks": [
                            {
                                "id": "task_01",
                                "title": "Polish layout",
                                "status": "in-progress",
                                "priority": "high",
                                "epic": "ui_polish_epic",
                            }
                        ],
                    },
                    "epics_summary": {
                        "total": 136,
                        "completed": 132,
                        "in_progress": 1,
                        "doing_count": 1,
                        "pending_count": 1,
                        "unstarted": 1,
                        "cancelled_count": 1,
                        "abandoned": 1,
                        "epics": [
                            {
                                "slug": "ui_polish_epic",
                                "title": "UI Polish Epic",
                                "status": "in_progress",
                                "execution_state": "doing",
                                "task_count": 4,
                                "pic": "danhdue",
                            }
                        ],
                    },
                    "heartbeat": {
                        "epic_slug": "ui_polish_epic",
                        "stage": "Stage 3 Phase 2 (TDD)",
                        "sub_step": "bdd_plan",
                        "events": events,
                    },
                    "agy_pool": {"state": "busy"},
                    "agy_profiles": [dict(item) for item in raw_agy_profiles],
                }
            )
        return repos, tracked

    class _FixtureHandler(http.server.BaseHTTPRequestHandler):
        def _json(self, code: int, body: dict[str, Any]) -> None:
            raw = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            if self.path == "/":
                raw = DASHBOARD_HTML.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            if self.path == "/api/tasks":
                repos, tracked = build_synthetic_repos()
                self._json(
                    200,
                    {
                        "workspace_root": str(ws),
                        "repos": repos,
                        "tracked_projects": tracked,
                        "available_profiles": ["danhdue", "tess"],
                    },
                )
                return
            if self.path == "/api/projects":
                tracked = check_tasks.load_tracked_projects(ws, cfg_path)
                effective = (
                    tracked
                    if tracked is not None
                    else check_tasks.build_initial_tracked_projects(ws)
                )
                suggestions = check_tasks.discover_untracked_workspace_repos(
                    ws, effective
                )
                self._json(
                    200,
                    {
                        "status": "ok",
                        "config_exists": tracked is not None,
                        "projects": effective,
                        "suggestions": suggestions,
                    },
                )
                return
            if self.path == "/api/profiles":
                self._json(200, {"profiles": ["danhdue", "tess"]})
                return
            self.send_error(404)

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            payload = (
                json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            )
            if self.path == "/api/projects/add":
                try:
                    res = check_tasks.add_tracked_project(
                        ws,
                        str(payload.get("path") or ""),
                        config_path=cfg_path,
                        index=payload.get("index"),
                    )
                    self._json(200, res)
                except ValueError as exc:
                    self._json(400, {"status": "error", "error": str(exc)})
                return
            if self.path == "/api/projects/remove":
                try:
                    res = check_tasks.remove_tracked_project(
                        ws,
                        name=str(payload.get("name") or ""),
                        config_path=cfg_path,
                    )
                    self._json(200, res)
                except ValueError as exc:
                    self._json(404, {"status": "error", "error": str(exc)})
                return
            if self.path == "/api/projects/browse/cancel":
                browse_cancel_count[0] += 1
                browse_cancel_event.set()
                self._json(200, {"status": "ok", "cancelled": True})
                return
            if self.path == "/api/projects/browse":
                browse_payloads.append(dict(payload))
                if len(browse_payloads) == 1:
                    browse_cancel_event.wait(timeout=5)
                    try:
                        self._json(200, {"status": "cancelled"})
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    return
                self._json(200, {"status": "ok", "path": str(ext_repo)})
                return
            if self.path in ("/api/agy-pool/priority", "/api/agy-pool/settings"):
                prof = str(payload.get("profile") or "").strip()
                prio = payload.get("priority")
                max_c = payload.get("max_concurrent")
                if prof not in fixture_pool_settings:
                    self._json(404, {"status": "error", "error": "Not in pool"})
                    return
                if prio is not None:
                    if not isinstance(prio, int) or isinstance(prio, bool) or prio < 1:
                        self._json(
                            400, {"status": "error", "error": "Invalid priority"}
                        )
                        return
                    fixture_pool_settings[prof]["priority"] = prio
                if max_c is not None:
                    if (
                        not isinstance(max_c, int)
                        or isinstance(max_c, bool)
                        or max_c < 0
                    ):
                        self._json(
                            400, {"status": "error", "error": "Invalid max_concurrent"}
                        )
                        return
                    fixture_pool_settings[prof]["max_concurrent"] = max_c
                pool_updates_received.append(dict(payload))
                pool_sorted = sorted(
                    [
                        {
                            "profile": k,
                            "priority": v["priority"],
                            "max_concurrent": v["max_concurrent"],
                        }
                        for k, v in fixture_pool_settings.items()
                    ],
                    key=lambda item: (item["priority"], item["profile"]),
                )
                self._json(
                    200,
                    {
                        "status": "ok",
                        "profile": prof,
                        "priority": fixture_pool_settings[prof]["priority"],
                        "max_concurrent": fixture_pool_settings[prof]["max_concurrent"],
                        "pool": pool_sorted,
                    },
                )
                return
            self._json(200, {"status": "ok"})

        def log_message(self, format: str, *args: Any) -> None:
            return

    class _ReuseTcpServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        allow_reuse_address = True
        daemon_threads = True

    srv = _ReuseTcpServer(("127.0.0.1", 0), _FixtureHandler)
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()

    cdp_helper = tmp_path / "cdp_helper.mjs"
    cdp_helper.write_text(_NODE_CDP_HELPER, encoding="utf-8")
    url = f"http://127.0.0.1:{port}/"

    script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(cdp_helper))};

async function waitFor(cdp, expr, label, timeoutMs = 10000) {{
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {{
    const val = await cdp.evaluate(expr);
    if (val) return val;
    await new Promise((r) => setTimeout(r, 80));
  }}
  throw new Error('Timed out waiting for: ' + label);
}}

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Emulation.setDeviceMetricsOverride', {{
    width: 1440,
    height: 1100,
    deviceScaleFactor: 1,
    mobile: false,
  }});
  await cdp.send('Page.navigate', {{ url: {json.dumps(url)} }});
  await waitFor(
    cdp,
    `Boolean(document.querySelector('#epics-overview-counts-D3Nexus') && document.querySelector('#agy-profiles-D3Nexus') && document.querySelector('[data-action="copy-event-logs"]'))`,
    'Dashboard initial render',
  );

  // 1. Epics Overview wrap-content width, top alignment, and Approval Blockers containment
  const overviewMetrics = await cdp.evaluate(`(() => {{
    const grid = document.getElementById('epics-overview-counts-D3Nexus');
    const overviewCard = grid.querySelector('[data-overview-card="epics-overview"]');
    const blockersCard = grid.querySelector('[data-overview-card="approval-blockers"]');
    const headerBar = overviewCard.children[0];
    const statsGrid = overviewCard.children[1];
    const statCards = Array.from(overviewCard.querySelectorAll('[data-overview-stat]'));

    const gridRect = grid.getBoundingClientRect();
    const ovRect = overviewCard.getBoundingClientRect();
    const blRect = blockersCard.getBoundingClientRect();
    const hdrRect = headerBar.getBoundingClientRect();
    const statsRect = statsGrid.getBoundingClientRect();

    return {{
      justifyContent: getComputedStyle(overviewCard).justifyContent,
      gridCols: getComputedStyle(grid).gridTemplateColumns,
      ovWidth: ovRect.width,
      blWidth: blRect.width,
      blRightOverflow: blRect.right - gridRect.right,
      blScrollOverflow: blockersCard.scrollWidth - blockersCard.clientWidth,
      headerToStatsGap: statsRect.top - hdrRect.bottom,
      statsHeightRatio: statsRect.height / ovRect.height,
      statCount: statCards.length,
      anyStatClipped: statCards.some((c) => c.scrollWidth > c.clientWidth + 2),
      statHeights: statCards.map((c) => Math.round(c.getBoundingClientRect().height)),
    }};
  }})()`);

  assert.ok(
    ['flex-start', 'start', 'flow-start'].includes(overviewMetrics.justifyContent),
    `Epics Overview must be top-aligned, got ${{overviewMetrics.justifyContent}}`,
  );
  assert.equal(overviewMetrics.statCount, 5);
  assert.equal(overviewMetrics.anyStatClipped, false, 'Epics Overview stat cards must never clip/crush');
  assert.ok(overviewMetrics.headerToStatsGap <= 20, `Expected top-aligned stat grid close to header, got gap=${{overviewMetrics.headerToStatsGap}}`);
  assert.ok(overviewMetrics.blRightOverflow <= 2, `Approval Blockers overflowed grid right edge by ${{overviewMetrics.blRightOverflow}}px`);
  assert.ok(overviewMetrics.blScrollOverflow <= 2, `Approval Blockers had horizontal overflow ${{overviewMetrics.blScrollOverflow}}px`);
  assert.ok(overviewMetrics.blWidth >= 400, `Approval Blockers should fill remaining width, got ${{overviewMetrics.blWidth}}px`);

  // 2. Execution Logs: permanently collapsed (4 lines) + Copy All 12 logs button
  const logsState = await cdp.evaluate(`(async () => {{
    window.__copiedLogs = [];
    Object.defineProperty(navigator, 'clipboard', {{
      configurable: true,
      value: {{
        writeText: async (txt) => {{
          window.__copiedLogs.push(String(txt));
        }},
      }},
    }});
    const logBox = document.querySelector('[data-telemetry="event-logs"]');
    const copyBtn = logBox.querySelector('[data-action="copy-event-logs"]');
    const visibleText = logBox.innerText;
    copyBtn.click();
    await new Promise((r) => setTimeout(r, 50));
    return {{
      visibleText,
      btnTextAfterClick: copyBtn.textContent.trim(),
      copied: window.__copiedLogs,
    }};
  }})()`);

  assert.ok(logsState.visibleText.includes('Execution Logs (12)'));
  assert.ok(logsState.visibleText.includes('Execution event line #12'));
  assert.equal(logsState.visibleText.includes('Execution event line #1\n'), false);
  assert.equal(logsState.visibleText.includes('Execution event line #4'), false);
  assert.equal(logsState.visibleText.includes('View all'), false);
  assert.equal(logsState.visibleText.includes('Collapse'), false);
  assert.equal(logsState.btnTextAfterClick, '✓ Copied');
  assert.equal(logsState.copied.length, 1);
  assert.equal(logsState.copied[0].split('\n').length, 12);
  assert.ok(logsState.copied[0].includes('Execution event line #1'));
  assert.ok(logsState.copied[0].includes('Execution event line #12'));

  // 3. Agy Profile Pool: priority (1..6) & concurrency (0..6) dropdowns, quota progress bars in the middle, task column at the far right
  const agyLayout = await cdp.evaluate(`(() => {{
    const rows = Array.from(document.querySelectorAll('#agy-profiles-D3Nexus tr[data-agy-profile-row]'));
    return rows.map((row) => {{
      const cols = Array.from(row.children).map((td) => td.getAttribute('data-agy-col'));
      const statusTd = row.querySelector('[data-agy-col="status"]');
      const prioSel = row.querySelector('select.select-agy-priority');
      const concSel = row.querySelector('select.select-agy-concurrency');
      const q5 = row.querySelector('[data-agy-col="quota-5h"]');
      const qw = row.querySelector('[data-agy-col="quota-weekly"]');
      const taskTd = row.querySelector('[data-agy-col="task"]');
      const fill5 = q5.querySelector('.agy-quota-progress-fill');
      const fillW = qw.querySelector('.agy-quota-progress-fill');
      return {{
        profile: row.getAttribute('data-agy-profile-row'),
        cols,
        priorityVal: prioSel ? prioSel.value : null,
        priorityOptions: prioSel ? Array.from(prioSel.options).map((o) => o.value) : [],
        isTopClass: prioSel ? prioSel.classList.contains('priority-top') : false,
        concVal: concSel ? concSel.value : null,
        concOptions: concSel ? Array.from(concSel.options).map((o) => o.value) : [],
        prioWidth: prioSel ? prioSel.getBoundingClientRect().width : 0,
        concWidth: concSel ? concSel.getBoundingClientRect().width : 0,
        prioAlign: prioSel ? getComputedStyle(prioSel).textAlign : '',
        concAlign: concSel ? getComputedStyle(concSel).textAlign : '',
        statusLeft: statusTd.getBoundingClientRect().left,
        prioLeft: prioSel.getBoundingClientRect().left,
        concLeft: concSel.getBoundingClientRect().left,
        q5Left: q5.getBoundingClientRect().left,
        qwLeft: qw.getBoundingClientRect().left,
        taskLeft: taskTd.getBoundingClientRect().left,
        fill5Width: fill5.style.width,
        fill5Color: getComputedStyle(fill5).backgroundColor,
        fillWWidth: fillW.style.width,
        fillWColor: getComputedStyle(fillW).backgroundColor,
      }};
    }});
  }})()`);

  assert.equal(agyLayout.length, 3);
  for (const r of agyLayout) {{
    assert.deepEqual(r.cols, ['profile', 'status', 'priority', 'concurrency', 'quota-5h', 'quota-weekly', 'task']);
    assert.deepEqual(r.priorityOptions, ['1', '2', '3', '4', '5', '6']);
    assert.deepEqual(r.concOptions, ['0', '1', '2', '3', '4', '5', '6']);
    assert.ok(r.statusLeft < r.prioLeft && r.prioLeft < r.concLeft && r.concLeft < r.q5Left, `Priority & concurrency must sit between status and quota for ${{r.profile}}`);
    assert.ok(r.q5Left < r.qwLeft && r.qwLeft < r.taskLeft, `Quota must be in middle and task on far right for ${{r.profile}}`);
    assert.ok(r.prioWidth <= 54 && r.concWidth <= 54, `Dropdowns must stay compact (got prio=${{r.prioWidth}}, conc=${{r.concWidth}})`);
    assert.equal(r.prioAlign, 'center');
    assert.equal(r.concAlign, 'center');
  }}
  assert.deepEqual(agyLayout.map((r) => [r.profile, r.priorityVal, r.concVal]), [
    ['khangatuaon248', '1', '6'],
    ['huynhminhtien0510', '2', '2'],
    ['hau', '3', '2'],
  ]);
  assert.equal(agyLayout[0].isTopClass, true);
  assert.equal(agyLayout[1].isTopClass, false);
  // khangatuaon248: 78.3% green, 92.0% green
  assert.equal(agyLayout[0].fill5Width, '78.3%');
  assert.equal(agyLayout[0].fill5Color, 'rgb(16, 185, 129)');
  // huynhminhtien0510: 28.4% amber
  assert.equal(agyLayout[1].fill5Width, '28.4%');
  assert.equal(agyLayout[1].fill5Color, 'rgb(245, 158, 11)');
  // hau: weekly 1.4% red
  assert.equal(agyLayout[2].fillWWidth, '1.4%');
  assert.equal(agyLayout[2].fillWColor, 'rgb(239, 68, 68)');

  // 3b. Change hau priority from P3 -> P1 and concurrency to 0 (Off) via dropdowns
  await cdp.evaluate(`(() => {{
    const sel = document.querySelector('#agy-profiles-D3Nexus select.select-agy-priority[data-agy-priority-profile="hau"]');
    sel.value = '1';
    sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
  }})()`);
  await waitFor(
    cdp,
    `(() => {{
      const rows = Array.from(document.querySelectorAll('#agy-profiles-D3Nexus tr[data-agy-profile-row]'));
      return rows.length === 3 && rows[0].getAttribute('data-agy-profile-row') === 'hau' && rows[0].querySelector('select.select-agy-priority')?.value === '1';
    }})()`,
    'Priority change re-orders hau to top as P1',
  );
  await cdp.evaluate(`(() => {{
    const sel = document.querySelector('#agy-profiles-D3Nexus select.select-agy-concurrency[data-agy-concurrency-profile="hau"]');
    sel.value = '0';
    sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
  }})()`);
  await waitFor(
    cdp,
    `(() => {{
      const row = document.querySelector('#agy-profiles-D3Nexus tr[data-agy-profile-row="hau"]');
      return Boolean(row && row.getAttribute('data-agy-disabled') === '1' && row.querySelector('select.select-agy-concurrency')?.classList.contains('concurrency-off') && row.querySelector('[data-agy-col="status"]')?.textContent.includes('disabled'));
    }})()`,
    'Setting hau concurrency to 0 marks row disabled with concurrency-off styling',
  );
  const afterSettings = await cdp.evaluate(`Array.from(document.querySelectorAll('#agy-profiles-D3Nexus tr[data-agy-profile-row]')).map((r) => [r.getAttribute('data-agy-profile-row'), r.querySelector('select.select-agy-priority').value, r.querySelector('select.select-agy-concurrency').value, r.getAttribute('data-agy-disabled')])`);
  assert.deepEqual(afterSettings, [
    ['hau', '1', '0', '1'],
    ['khangatuaon248', '1', '6', '0'],
    ['huynhminhtien0510', '2', '2', '0'],
  ]);

  // 4. Long-click header bar -> Edit Mode (+ Add Project far right vertically centered, close button on each tab)
  const beforeEdit = await cdp.evaluate(`({{
    hasAdd: Boolean(document.getElementById('btn-add-project')),
    closeCount: document.querySelectorAll('.repo-tab-close-btn').length,
  }})`);
  assert.equal(beforeEdit.hasAdd, false);
  assert.equal(beforeEdit.closeCount, 0);

  await cdp.evaluate(`(() => {{
    const bar = document.getElementById('repo-tab-bar');
    const r = bar.getBoundingClientRect();
    bar.dispatchEvent(new PointerEvent('pointerdown', {{ bubbles: true, button: 0, clientX: r.left + 10, clientY: r.top + 10 }}));
  }})()`);
  await new Promise((r) => setTimeout(r, 600));
  await cdp.evaluate(`(() => {{
    const bar = document.getElementById('repo-tab-bar');
    bar.dispatchEvent(new PointerEvent('pointerup', {{ bubbles: true, button: 0 }}));
  }})()`);

  const editGeometry = await cdp.evaluate(`(() => {{
    const bar = document.getElementById('repo-tab-bar');
    const addBtn = document.getElementById('btn-add-project');
    const tabs = Array.from(bar.querySelectorAll('.repo-tab-btn'));
    const closeBtns = Array.from(bar.querySelectorAll('.repo-tab-close-btn'));
    const barRect = bar.getBoundingClientRect();
    const addRect = addBtn.getBoundingClientRect();
    const lastTabRect = tabs[tabs.length - 1].getBoundingClientRect();
    return {{
      isEditClass: bar.classList.contains('edit-mode'),
      isLastChild: bar.lastElementChild === addBtn,
      tabCount: tabs.length,
      closeCount: closeBtns.length,
      addRightOfLastTab: addRect.left >= lastTabRect.right - 1,
      verticalCenterDelta: Math.abs((addRect.top + addRect.height / 2) - (barRect.top + barRect.height / 2)),
    }};
  }})()`);

  assert.equal(editGeometry.isEditClass, true);
  assert.equal(editGeometry.isLastChild, true, '+ Add Project must be the rightmost element in header bar');
  assert.equal(editGeometry.closeCount, editGeometry.tabCount, 'Every project tab must display a close button in edit mode');
  assert.equal(editGeometry.addRightOfLastTab, true);
  assert.ok(editGeometry.verticalCenterDelta <= 4, `Expected + Add Project vertically centered, delta=${{editGeometry.verticalCenterDelta}}px`);

  // 5a. Open Add Project modal, click Browse Finder, then close modal -> auto-cancels open Finder without error
  await cdp.evaluate(`document.getElementById('btn-add-project').click()`);
  await waitFor(
    cdp,
    `document.getElementById('modal-add-project').style.display === 'flex' && document.querySelectorAll('#add-project-suggestions .project-suggestion-chip').length === 1`,
    'Add Project modal open with suggestion chip',
  );
  await cdp.evaluate(`document.getElementById('btn-browse-project-folder').click()`);
  await waitFor(
    cdp,
    `document.getElementById('btn-browse-project-folder').disabled === true`,
    'Browse Finder enters pending state',
  );
  await cdp.evaluate(`document.querySelector('#modal-add-project .modal-close-btn').click()`);
  await waitFor(
    cdp,
    `document.getElementById('modal-add-project').style.display === 'none' && document.getElementById('btn-browse-project-folder').disabled === false`,
    'Closing Add Project modal auto-cancels pending Finder and restores button',
  );
  const cancelErrVisible = await cdp.evaluate(`document.getElementById('add-project-error').style.display`);
  assert.equal(cancelErrVisible, 'none', 'Closing modal while Finder is open must not show an error banner');

  // 5b. Re-open Add Project modal, click Browse Finder -> fills path -> submit adds external repo
  await cdp.evaluate(`document.getElementById('btn-add-project').click()`);
  await waitFor(
    cdp,
    `document.getElementById('modal-add-project').style.display === 'flex'`,
    'Add Project modal re-opened',
  );
  await cdp.evaluate(`document.getElementById('btn-browse-project-folder').click()`);
  await waitFor(
    cdp,
    `document.getElementById('add-project-path-input').value.includes('custom-mobile')`,
    'Browse Finder populates path input',
  );
  await cdp.evaluate(`document.getElementById('btn-submit-add-project').click()`);
  await waitFor(
    cdp,
    `Boolean(document.querySelector('#repo-tab-bar .repo-tab-btn[data-tab="custom-mobile"]'))`,
    'Newly added custom-mobile repo tab appears',
  );

  // 6. Remove custom-mobile via close button -> toast shows Undo -> click Undo restores it
  await cdp.evaluate(`document.querySelector('.repo-tab-close-btn[data-remove-repo="custom-mobile"]').click()`);
  await waitFor(
    cdp,
    `!document.querySelector('#repo-tab-bar .repo-tab-btn[data-tab="custom-mobile"]') && document.getElementById('toast-action-btn').style.display === 'inline-flex'`,
    'Removed tab disappears and Undo toast appears',
  );
  await cdp.evaluate(`document.getElementById('toast-action-btn').click()`);
  await waitFor(
    cdp,
    `Boolean(document.querySelector('#repo-tab-bar .repo-tab-btn[data-tab="custom-mobile"]'))`,
    'Undo restores removed project tab',
  );

  // 7. Reload page with custom-mobile selected -> stays on custom-mobile immediately (no reset to D3Nexus)
  await cdp.send('Page.reload', {{ ignoreCache: true }});
  await waitFor(
    cdp,
    `Boolean(document.getElementById('repo-detail-content-custom-mobile'))`,
    'Reload preserves custom-mobile saved tab and renders it directly',
  );
  const reloadedActive = await cdp.evaluate(`localStorage.getItem('check_tasks_active_focus_tab')`);
  assert.equal(reloadedActive, 'custom-mobile');

  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{JSON.stringify(cdp.consoleErrors)}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{JSON.stringify(cdp.runtimeExceptions)}}`);
  console.log(JSON.stringify({{ ok: true, overviewMetrics, agyLayout, editGeometry }}));
}} finally {{
  await cdp.close();
}}
"""
    try:
        res = _run_node_script(script, timeout=45)
        assert res.get("ok") is True
        assert browse_cancel_count[0] == 1, (
            f"Expected closing modal to trigger /api/projects/browse/cancel once, got {browse_cancel_count[0]}"
        )
        assert len(browse_payloads) >= 2
        for bp in browse_payloads:
            wb = bp.get("windowBounds")
            assert isinstance(wb, dict), (
                f"Expected windowBounds in browse payload: {bp}"
            )
            assert wb.get("width", 0) > 0 and wb.get("height", 0) > 0, wb
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=5)
