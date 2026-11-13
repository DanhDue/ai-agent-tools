"""Unit and integration tests for Check-Tasks harvester, ledger union, 96% backend, and PIC sync.

Covers BDD Scenarios:
- RSDH-HP-06: PIC reassignment synchronizes root and worktree PIC-bearing files while preserving review and BDD prose
- RSDH-EC-04: Check-Tasks harvester leaves idle repositories without active worktrees or tasks in Idle state
- RSDH-EC-05: PIC reassignment validates profile names and isolates sibling epics across worktrees
- RSDH-ST-02: Gate ledger unification merges root and worktree JSONL and GATE_LEDGER.md entries
- RSDH-ST-04: extract_epic_pic resolves PIC across root and worktree handoff placeholders cleanly
- RSDH-AR-03: Check-tasks harvester isolates multi-epic decisions, exposes live quality_runs, and expires stale owners
- RSDH-FR-04: Partial read-only failure during PIC reassignment reports warnings without corrupting sibling files
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
CHECK_TASKS_SCRIPTS = (
    REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
)
for _p in (str(SCRIPTS_DIR), str(CHECK_TASKS_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _state_envelope  # type: ignore[import-not-found]
import check_tasks  # type: ignore[import-not-found]
import tasks_server  # type: ignore[import-not-found]


def _git(cwd: Path, *args: str) -> str:
    """Run git in cwd and return stripped stdout."""
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _init_git_repo(repo_dir: Path) -> Path:
    """Initialize a clean git repository on branch main with one initial commit."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    _git(repo_dir, "init", "-b", "main")
    _git(repo_dir, "config", "user.email", "test@rsdh.local")
    _git(repo_dir, "config", "user.name", "RSDH Tester")
    (repo_dir / "README.md").write_text("# Demo Repo\n", encoding="utf-8")
    _git(repo_dir, "add", "README.md")
    _git(repo_dir, "commit", "-m", "Initial commit")
    return repo_dir


def _add_worktree(repo_dir: Path, wt_path: Path, branch_name: str) -> Path:
    """Create a linked git worktree for branch_name."""
    wt_path.parent.mkdir(parents=True, exist_ok=True)
    _git(repo_dir, "worktree", "add", "-b", branch_name, str(wt_path))
    return wt_path


def _find_dead_pid() -> int:
    """Return a high local PID that is guaranteed not to exist."""
    for candidate in range(950000, 999999):
        try:
            os.kill(candidate, 0)
        except ProcessLookupError:
            return candidate
        except PermissionError:
            continue
    raise AssertionError("Unable to locate an unused PID")


def _seed_epic_checkout(
    checkout_root: Path,
    epic_slug: str,
    pic_value: str,
    *,
    include_vscode: bool = False,
) -> dict[str, Path]:
    """Populate realistic PIC-bearing and protected prose artifacts in a checkout."""
    epic_dir = checkout_root / ".devtool" / "epic" / epic_slug
    epic_dir.mkdir(parents=True, exist_ok=True)
    features_dir = checkout_root / ".devtool" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    state_dir = checkout_root / ".devtool" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    en_hld = epic_dir / f"{epic_slug}.en.md"
    en_hld.write_text(
        f"# Epic: {epic_slug}\n\n"
        "## Meta Data\n\n"
        f"- **Epic name**: `{epic_slug}`\n"
        f"- **PIC**: `{pic_value}`\n"
        "- **Status**: In Progress\n",
        encoding="utf-8",
    )

    vi_hld = epic_dir / f"{epic_slug}.vi.md"
    vi_hld.write_text(
        f"# Epic: {epic_slug}\n\n"
        "## Thông Tin Chung\n\n"
        f"- **Tên Epic**: `{epic_slug}`\n"
        f"- **PIC**: `{pic_value}`\n"
        "- **Trạng thái**: Đang thực hiện\n",
        encoding="utf-8",
    )

    design_spec = epic_dir / f"2026-11-13-{epic_slug}-design.en.md"
    design_spec.write_text(
        f"# {epic_slug} Design Spec\n\n"
        f"- **Epic Directory**: `{epic_slug}`\n"
        "- **Status**: Approved (Gate 1)\n",
        encoding="utf-8",
    )

    handoff = epic_dir / "handoff.md"
    handoff.write_text(
        f"# Handoff: {epic_slug}\n\n"
        "## Status\n\n"
        "- **Packaged**: 2026-11-13\n"
        f"- **PIC / Assigned Profile**: @{pic_value}\n"
        "- **Gates passed**: 1, 2\n",
        encoding="utf-8",
    )

    epic_task = epic_dir / "task_01_core.md"
    epic_task.write_text(
        "---\n"
        'id: "task_01_core"\n'
        'status: "in-progress"\n'
        f'epic: "{epic_slug}"\n'
        f'pic: "{pic_value}"\n'
        "---\n\n# Task 1: Core\n",
        encoding="utf-8",
    )

    feat_task = features_dir / f"task_02_{epic_slug}_feature.md"
    feat_task.write_text(
        "---\n"
        f'id: "task_02_{epic_slug}_feature"\n'
        'status: "todo"\n'
        f'epic: "{epic_slug}"\n'
        f'pic: "{pic_value}"\n'
        "---\n\n# Task 2: Feature\n",
        encoding="utf-8",
    )

    pipeline_json = state_dir / f"{epic_slug}.pipeline.json"
    pipeline_json.write_text(
        json.dumps({"epic": epic_slug, "pic": pic_value, "stage": "Stage 3"}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    bdd_file = epic_dir / "bdd_scenarios.en.md"
    bdd_file.write_text(
        "# BDD Scenarios\n\n"
        "```gherkin\n"
        "Scenario: [DEMO-HP-01] Sample\n"
        "Given state\n"
        "Then unchanged\n"
        "```\n",
        encoding="utf-8",
    )

    principal_review = epic_dir / "principal_review.md"
    principal_review.write_text(
        "# Principal Review\n\n- **Overall Verdict**: PASS\n",
        encoding="utf-8",
    )

    review_results = epic_dir / "review_results.md"
    review_results.write_text(
        "# Cross-Model Review\n\n- **Overall Verdict**: CONVERGED (PASS)\n",
        encoding="utf-8",
    )

    fix_plan = epic_dir / "fix_plan_round1.md"
    fix_plan.write_text(
        "# Fix Plan Round 1\n\n- Keep original prose untouched.\n",
        encoding="utf-8",
    )

    smoke = epic_dir / "manual_smoke_checklist.md"
    smoke.write_text(
        "# Manual Smoke Checklist\n\n- Verify manually.\n",
        encoding="utf-8",
    )

    paths: dict[str, Path] = {
        "en_hld": en_hld,
        "vi_hld": vi_hld,
        "design_spec": design_spec,
        "handoff": handoff,
        "epic_task": epic_task,
        "feat_task": feat_task,
        "pipeline_json": pipeline_json,
        "bdd_file": bdd_file,
        "principal_review": principal_review,
        "review_results": review_results,
        "fix_plan": fix_plan,
        "smoke": smoke,
    }

    if include_vscode:
        vscode_dir = checkout_root / ".vscode"
        vscode_dir.mkdir(parents=True, exist_ok=True)
        settings = vscode_dir / "settings.json"
        settings.write_text(
            json.dumps(
                {"window.title": f"[DEMO] [@{pic_value}] {epic_slug}"},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        paths["vscode_settings"] = settings

    return paths


class TestRsdhHarvesterAndPic_Integration:
    """Integration suite for Check-Tasks harvester, ledger union, 96% backend, and PIC sync."""

    def test_rsdh_hp_06_pic_root_worktree_sync(self, tmp_path: Path) -> None:
        """[RSDH-HP-06] [Tier C - Integration] PIC reassignment synchronizes root and worktree PIC-bearing files while preserving review and BDD prose."""
        repo = _init_git_repo(tmp_path / "demo-repo")
        root_files = _seed_epic_checkout(repo, "demo_epic", "mommy", include_vscode=True)

        # Add an unrelated sibling task in root .devtool/features/ that must stay untouched
        sibling_feat = repo / ".devtool" / "features" / "task_99_sibling.md"
        sibling_feat.write_text(
            '---\nid: "task_99_sibling"\nstatus: "todo"\nepic: "sibling_epic"\npic: "alice"\n---\n# Sibling Task\n',
            encoding="utf-8",
        )
        sibling_before = sibling_feat.read_bytes()
        root_vscode_before = root_files["vscode_settings"].read_bytes()

        wt = _add_worktree(repo, repo / ".worktrees" / "demo_epic", "epic/demo-epic")
        wt_files = _seed_epic_checkout(wt, "demo_epic", "mommy", include_vscode=True)

        # Seed synchronized heartbeat JSON across root and worktree
        _state_envelope.update_epic_heartbeat(
            wt,
            "demo_epic",
            stage="Stage 3 Phase 2 (TDD)",
            pic="mommy",
            last_event="Initial heartbeat",
        )

        protected_keys = (
            "bdd_file",
            "principal_review",
            "review_results",
            "fix_plan",
            "smoke",
        )
        root_protected_bytes = {k: root_files[k].read_bytes() for k in protected_keys}
        wt_protected_bytes = {k: wt_files[k].read_bytes() for k in protected_keys}

        result = tasks_server.assign_epic_pic(tmp_path, "demo-repo", "demo_epic", "brother")

        assert result["status"] == "ok"
        assert result["pic"] == "brother"
        assert result.get("warnings") == []
        assert len(result["updated_files"]) >= 12

        for checkout_files in (root_files, wt_files):
            assert "`brother`" in checkout_files["en_hld"].read_text(encoding="utf-8")
            assert "`brother`" in checkout_files["vi_hld"].read_text(encoding="utf-8")
            assert "- **PIC**: `brother`" in checkout_files["design_spec"].read_text(
                encoding="utf-8"
            )
            assert (
                "- **PIC / Assigned Profile**: `brother`"
                in checkout_files["handoff"].read_text(encoding="utf-8")
            )
            assert 'pic: "brother"' in checkout_files["epic_task"].read_text(
                encoding="utf-8"
            )
            assert 'pic: "brother"' in checkout_files["feat_task"].read_text(
                encoding="utf-8"
            )
            pipeline_data = json.loads(
                checkout_files["pipeline_json"].read_text(encoding="utf-8")
            )
            assert pipeline_data["pic"] == "brother"

        for base in (repo, wt):
            hb_data = json.loads(
                (base / ".devtool" / "state" / "demo_epic.heartbeat.json").read_text(
                    encoding="utf-8"
                )
            )
            assert hb_data["pic"] == "brother"

        wt_settings_data = json.loads(
            wt_files["vscode_settings"].read_text(encoding="utf-8")
        )
        assert "[@brother]" in wt_settings_data["window.title"]

        # Root .vscode/settings.json and sibling epic task must remain untouched
        assert root_files["vscode_settings"].read_bytes() == root_vscode_before
        assert sibling_feat.read_bytes() == sibling_before

        # Review and BDD prose files must remain byte-for-byte unchanged
        for k in protected_keys:
            assert root_files[k].read_bytes() == root_protected_bytes[k]
            assert wt_files[k].read_bytes() == wt_protected_bytes[k]

    def test_rsdh_ec_04_idle_repo_no_alphabetical_fallback(self, tmp_path: Path) -> None:
        """[RSDH-EC-04] [Tier A - Unit] Check-Tasks harvester leaves idle repositories without active worktrees or tasks in Idle state."""
        repo = _init_git_repo(tmp_path / "idle-repo")
        for slug in ("alpha_dormant", "choosing_a_lifecycle"):
            ep_dir = repo / ".devtool" / "epic" / slug
            ep_dir.mkdir(parents=True, exist_ok=True)
            (ep_dir / f"{slug}.en.md").write_text(
                f"# {slug}\n\n- **Status**: Backlog\n",
                encoding="utf-8",
            )

        assert check_tasks.resolve_active_epic(repo) is None
        decision = check_tasks.derive_lifecycle_state(repo, None)
        assert decision.stage_name == check_tasks.LifecycleStage.IDLE.value
        assert decision.is_human_action_required is False

        meta = check_tasks.scan_repo(repo)
        assert meta.active_epic is None
        assert meta.active_stage == check_tasks.LifecycleStage.IDLE.value
        assert meta.is_human_action_required is False

        # Preserve Strategy 6: active task in .devtool/features/ still resolves epic
        features_dir = repo / ".devtool" / "features"
        features_dir.mkdir(parents=True, exist_ok=True)
        (features_dir / "task_01_live.md").write_text(
            '---\nid: "task_01_live"\nstatus: "in-progress"\nepic: "live-feat"\n---\n# Live Task\n',
            encoding="utf-8",
        )
        assert check_tasks.resolve_active_epic(repo) == "live-feat"

    def test_rsdh_ec_05_pic_validation_http_400_and_sibling_isolation(
        self,
        tmp_path: Path,
    ) -> None:
        """[RSDH-EC-05] [Tier A - Unit] PIC reassignment validates profile names and isolates sibling epics across worktrees."""
        repo = _init_git_repo(tmp_path / "multi-epic-repo")
        demo_root = _seed_epic_checkout(repo, "demo_epic", "mommy")
        sibling_root = _seed_epic_checkout(repo, "sibling_epic", "alice")

        demo_wt = _add_worktree(repo, repo / ".worktrees" / "demo_epic", "epic/demo-epic")
        demo_wt_files = _seed_epic_checkout(
            demo_wt, "demo_epic", "mommy", include_vscode=True
        )

        sibling_wt = _add_worktree(
            repo, repo / ".worktrees" / "sibling_epic", "epic/sibling-epic"
        )
        sibling_wt_files = _seed_epic_checkout(
            sibling_wt, "sibling_epic", "alice", include_vscode=True
        )

        sibling_snapshots = {
            f"root_{k}": p.read_bytes() for k, p in sibling_root.items()
        } | {f"wt_{k}": p.read_bytes() for k, p in sibling_wt_files.items()}
        demo_before = demo_root["en_hld"].read_bytes()

        with pytest.raises(ValueError):
            tasks_server.assign_epic_pic(tmp_path, "multi-epic-repo", "demo_epic", "../bad")
        with pytest.raises(ValueError):
            tasks_server.assign_epic_pic(tmp_path, "multi-epic-repo", "../bad_epic", "tess")
        assert demo_root["en_hld"].read_bytes() == demo_before

        port = tasks_server.find_available_port(18850)
        pid_file = tmp_path / "tasks_server_ec05.pid"
        server = tasks_server.TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=tmp_path,
            pid_file=pid_file,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.1)

        try:
            # Malformed PIC must return HTTP 400 JSON error, never HTTP 500
            bad_req = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/api/epic/pic",
                data=json.dumps(
                    {"repo": "multi-epic-repo", "epic": "demo_epic", "pic": "../bad"}
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(bad_req, timeout=3)
            assert exc_info.value.code == 400
            err_payload = json.loads(exc_info.value.read().decode("utf-8"))
            assert err_payload.get("status") == "error"

            # Valid PIC updates demo_epic across root and demo_wt while isolating sibling_epic
            ok_req = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/api/epic/pic",
                data=json.dumps(
                    {"repo": "multi-epic-repo", "epic": "demo_epic", "pic": "tess"}
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(ok_req, timeout=3) as resp:
                assert resp.status == 200
                ok_payload = json.loads(resp.read().decode("utf-8"))
                assert ok_payload["status"] == "ok"
                assert ok_payload["pic"] == "tess"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2.0)

        assert "`tess`" in demo_root["en_hld"].read_text(encoding="utf-8")
        assert "`tess`" in demo_wt_files["en_hld"].read_text(encoding="utf-8")
        assert "[@tess]" in demo_wt_files["vscode_settings"].read_text(encoding="utf-8")

        for k, path in sibling_root.items():
            assert path.read_bytes() == sibling_snapshots[f"root_{k}"]
        for k, path in sibling_wt_files.items():
            assert path.read_bytes() == sibling_snapshots[f"wt_{k}"]

    def test_rsdh_st_02_gate_ledger_union_root_and_worktree(
        self, tmp_path: Path
    ) -> None:
        """[RSDH-ST-02] [Tier C - Integration] Gate ledger unification merges root and worktree JSONL and GATE_LEDGER.md entries."""
        repo = _init_git_repo(tmp_path / "ledger-repo")
        wt = _add_worktree(repo, repo / ".worktrees" / "demo_epic", "epic/demo-epic")

        # Root has older gate_ledger.jsonl with Gate 1 only
        root_state = repo / ".devtool" / "state"
        root_state.mkdir(parents=True, exist_ok=True)
        gate1 = {
            "timestamp": "2026-11-11T01:00:00Z",
            "epic": "demo_epic",
            "gate": 1,
            "commit": "aaa1111",
            "approved": "Gate 1 Spec",
            "deviations": "",
            "by": "developer",
        }
        (root_state / "gate_ledger.jsonl").write_text(
            json.dumps(gate1) + "\n", encoding="utf-8"
        )

        # Root GATE_LEDGER.md adds Gate 2 (alongside duplicate Gate 1)
        (repo / ".devtool" / "GATE_LEDGER.md").write_text(
            "# Gate Ledger\n\n"
            "| Timestamp | Epic | Gate | Commit | Approved Scope | Deviations | By |\n"
            "|---|---|---|---|---|---|---|\n"
            "| 2026-11-11T01:00:00Z | demo_epic | 1 | aaa1111 | Gate 1 Spec |  | developer |\n"
            "| 2026-11-11T02:00:00Z | demo_epic | 2 | bbb2222 | Gate 2 HLD |  | developer |\n",
            encoding="utf-8",
        )

        # Worktree GATE_LEDGER.md has Gate 3 and a sibling epic Gate 5 that must be ignored
        wt_devtool = wt / ".devtool"
        wt_devtool.mkdir(parents=True, exist_ok=True)
        (wt_devtool / "GATE_LEDGER.md").write_text(
            "# Gate Ledger\n\n"
            "| Timestamp | Epic | Gate | Commit | Approved Scope | Deviations | By |\n"
            "|---|---|---|---|---|---|---|\n"
            "| 2026-11-11T03:00:00Z | demo-epic | 3 | ccc3333 | Gate 3 Order |  | developer |\n"
            "| 2026-11-11T04:00:00Z | sibling-epic | 5 | ddd4444 | Sibling Done |  | developer |\n",
            encoding="utf-8",
        )

        entries = check_tasks.parse_gate_ledger_entries(repo, "demo_epic")
        gates = [int(e["gate"]) for e in entries]
        assert gates == [1, 2, 3]

        # Lifecycle FSM must advance past Gate 2 using merged Gate 3 approval
        features_dir = wt / ".devtool" / "features"
        features_dir.mkdir(parents=True, exist_ok=True)
        (features_dir / "task_01.md").write_text(
            '---\nid: "task_01"\nstatus: "in-progress"\nepic: "demo_epic"\n---\n# Task 1\n',
            encoding="utf-8",
        )
        decision = check_tasks.derive_lifecycle_state(repo, "demo_epic")
        assert decision.stage_name == check_tasks.LifecycleStage.STAGE_3_PHASE_2_TDD.value
        assert decision.is_human_action_required is False

    def test_rsdh_st_04_extract_epic_pic_worktree_and_placeholders(
        self,
        tmp_path: Path,
    ) -> None:
        """[RSDH-ST-04] [Tier A - Unit] extract_epic_pic resolves PIC across root and worktree handoff placeholders cleanly."""
        repo = _init_git_repo(tmp_path / "pic-extract-repo")
        root_epic = repo / ".devtool" / "epic" / "demo_epic"
        root_epic.mkdir(parents=True, exist_ok=True)
        (root_epic / "demo_epic.en.md").write_text(
            "# Epic: demo_epic\n\n- **Epic name**: `demo_epic`\n",
            encoding="utf-8",
        )

        wt = _add_worktree(repo, repo / ".worktrees" / "demo_epic", "epic/demo-epic")
        wt_epic = wt / ".devtool" / "epic" / "demo_epic"
        wt_epic.mkdir(parents=True, exist_ok=True)
        wt_handoff = wt_epic / "handoff.md"
        wt_handoff.write_text(
            "# Handoff\n\n- **PIC / Assigned Profile**: @danhdue\n",
            encoding="utf-8",
        )

        assert check_tasks.extract_epic_pic(repo, "demo_epic") == "danhdue"

        for placeholder in (
            "<unassigned>",
            "`<profile_account_id>` (e.g. `danhdue`)",
            "None",
            "null",
        ):
            wt_handoff.write_text(
                f"# Handoff\n\n- **PIC / Assigned Profile**: {placeholder}\n",
                encoding="utf-8",
            )
            assert check_tasks.extract_epic_pic(repo, "demo_epic") is None

    def test_rsdh_ar_03_multi_epic_isolation_quality_runs_and_stale_expiry(
        self,
        tmp_path: Path,
    ) -> None:
        """[RSDH-AR-03] [Tier C - Integration] Check-tasks harvester isolates multi-epic decisions, exposes live quality_runs, and expires stale owners."""
        repo = _init_git_repo(tmp_path / "ar03-repo")
        _seed_epic_checkout(repo, "epic-a", "brother")
        _seed_epic_checkout(repo, "epic-b", "tess")
        wt_a = _add_worktree(repo, repo / ".worktrees" / "epic-a", "epic/epic-a")
        _seed_epic_checkout(wt_a, "epic-a", "brother")

        # Record namespaced decisions for both epics (epic-a active via worktree, epic-b sibling)
        _state_envelope.record_pending_decision(
            wt_a,
            "epic-a",
            "Approve epic-a Gate 2 design",
            kind="gate_2_choice",
            decision_id="dec-a",
            stage="Stage 2 (Architecture)",
        )
        _state_envelope.record_pending_decision(
            repo,
            "epic-b",
            "Approve epic-b Gate 1 spec",
            kind="gate_1_spec",
            decision_id="dec-b",
            stage="Stage 1 (Inception)",
        )
        _state_envelope.update_epic_heartbeat(
            wt_a,
            "epic-a",
            stage="Stage 2 (Architecture)",
            active_wave=1,
            active_tasks=["task_01_core"],
            slots={"1": {"task_id": "task_01_core", "status": "working"}},
            last_event="Wave 1 started",
        )

        now = datetime.now(timezone.utc)
        fresh_iso = now.isoformat(timespec="seconds")
        expired_iso = (now - timedelta(seconds=900)).isoformat(timespec="seconds")
        dead_pid = _find_dead_pid()

        # Case 1: epic-a has ONLY a dead-PID/expired-TTL stale run while epic-b has a live concurrent run
        _state_envelope.update_quality_run(
            wt_a,
            "run-stale-a",
            epic_slug="epic-a",
            profile="epic",
            status="running",
            provider="python-qa",
            capability="test",
            pid=dead_pid,
            ttl_sec=60,
            started_at=expired_iso,
            updated_at=expired_iso,
        )
        _state_envelope.update_quality_run(
            repo,
            "run-live-b",
            epic_slug="epic-b",
            profile="pr",
            status="running",
            provider="python-qa",
            capability="lint",
            pid=os.getpid(),
            ttl_sec=300,
            started_at=fresh_iso,
            updated_at=fresh_iso,
        )

        meta1 = check_tasks.scan_repo(repo)
        assert meta1.active_epic == "epic-a"
        assert meta1.is_human_action_required is True
        assert meta1.prompt == "Approve epic-a Gate 2 design"
        assert meta1.pending_decision is not None
        assert meta1.pending_decision["epic"] == "epic-a"
        assert meta1.pending_decision["decision_id"] == "dec-a"
        assert meta1.heartbeat is not None
        assert meta1.heartbeat["active_wave"] == 1

        # Expired/dead-PID run must transition to "stale" (no permanent running banner)
        assert meta1.quality_active is not None
        assert meta1.quality_active["run_id"] == "run-stale-a"
        assert meta1.quality_active["status"] == "stale"
        # Concurrent live run surfaces via quality_runs without expired stale runs
        live_ids_1 = [r["run_id"] for r in meta1.quality_runs]
        assert live_ids_1 == ["run-live-b"]

        # Case 2: Add live run for epic-a and clear ONLY epic-a's pending decision
        _state_envelope.update_quality_run(
            wt_a,
            "run-live-a",
            epic_slug="epic-a",
            profile="epic",
            status="running",
            provider="python-qa",
            capability="type_check",
            pid=os.getpid(),
            ttl_sec=300,
            started_at=fresh_iso,
            updated_at=fresh_iso,
        )
        _state_envelope.clear_pending_decision(wt_a, "epic-a", decision_id="dec-a")

        meta2 = check_tasks.scan_repo(repo)
        assert meta2.active_epic == "epic-a"
        # Sibling epic-b's pending_decision must NOT bleed onto epic-a
        assert meta2.pending_decision is None
        assert meta2.is_human_action_required is False
        assert meta2.quality_active is not None
        assert meta2.quality_active["run_id"] == "run-live-a"
        assert meta2.quality_active["status"] == "running"
        assert {r["run_id"] for r in meta2.quality_runs} == {"run-live-a", "run-live-b"}

        # Check 96% pre-finish / 95% in-progress backend ceiling inside task_progress
        for wt_task in (
            wt_a / ".devtool" / "features" / "task_02_epic-a_feature.md",
            wt_a / ".devtool" / "epic" / "epic-a" / "task_01_core.md",
            repo / ".devtool" / "features" / "task_02_epic-a_feature.md",
            repo / ".devtool" / "epic" / "epic-a" / "task_01_core.md",
        ):
            txt = wt_task.read_text(encoding="utf-8")
            txt = txt.replace('status: "in-progress"', 'status: "done"').replace(
                'status: "todo"', 'status: "done"'
            )
            wt_task.write_text(txt, encoding="utf-8")
        # Remove sibling epic-b dir so only epic-a tasks are counted
        for f in (repo / ".devtool" / "features").glob("*epic-b*"):
            f.unlink()
        meta_pre_conv = check_tasks.scan_repo(repo)
        assert (
            meta_pre_conv.task_progress.done_tasks
            == meta_pre_conv.task_progress.total_tasks
        )
        assert meta_pre_conv.task_progress.percentage == 96.0

    def test_rsdh_fr_04_partial_readonly_failure_warnings_and_counts(
        self,
        tmp_path: Path,
    ) -> None:
        """[RSDH-FR-04] [Tier C - Integration] Partial read-only failure during PIC reassignment reports warnings without corrupting sibling files."""
        repo = _init_git_repo(tmp_path / "fr04-repo")
        files = _seed_epic_checkout(repo, "demo_epic", "mommy")
        # Remove optional state file to ensure missing optional state files do not fail or warn
        files["pipeline_json"].unlink()

        readonly_vi = files["vi_hld"]
        readonly_vi.chmod(0o444)
        try:
            res = tasks_server.assign_epic_pic(
                tmp_path, "fr04-repo", "demo_epic", "brother"
            )
        finally:
            readonly_vi.chmod(0o644)

        assert res["status"] == "ok"
        assert "`brother`" in files["en_hld"].read_text(encoding="utf-8")
        assert "- **PIC / Assigned Profile**: `brother`" in files["handoff"].read_text(
            encoding="utf-8"
        )
        assert 'pic: "brother"' in files["epic_task"].read_text(encoding="utf-8")
        # Unwritable .vi.md kept original content and triggered a warning
        assert "`mommy`" in readonly_vi.read_text(encoding="utf-8")
        warnings = res.get("warnings", [])
        assert any("demo_epic.vi.md" in w for w in warnings)
        assert all("demo_epic.vi.md" not in p for p in res["updated_files"])
        assert res["updated_count"] == len(res["updated_files"])
        assert res["updated_count"] > 0

    def test_backend_progress_ceiling_tiers(self, tmp_path: Path) -> None:
        """Verify extract_task_progress enforces <=95% incomplete, 96% pre-convergence, and 100% Waiting Finish / Done."""
        repo = _init_git_repo(tmp_path / "pct-repo")
        epic_dir = repo / ".devtool" / "epic" / "pct_epic"
        epic_dir.mkdir(parents=True, exist_ok=True)
        features_dir = repo / ".devtool" / "features"
        features_dir.mkdir(parents=True, exist_ok=True)

        # 19/20 done -> 95.0%, 99/100 would also cap at 95.0%
        for idx in range(1, 21):
            status = "done" if idx <= 19 else "in-progress"
            (features_dir / f"task_{idx:02d}.md").write_text(
                f'---\nid: "task_{idx:02d}"\nstatus: "{status}"\nepic: "pct_epic"\n---\n# Task {idx}\n',
                encoding="utf-8",
            )
        prog_incomplete = check_tasks.extract_task_progress(repo, "pct_epic")
        assert prog_incomplete.percentage == 95.0

        # 20/20 done pre-convergence -> 96.0%
        (features_dir / "task_20.md").write_text(
            '---\nid: "task_20"\nstatus: "done"\nepic: "pct_epic"\n---\n# Task 20\n',
            encoding="utf-8",
        )
        prog_pre_conv = check_tasks.extract_task_progress(repo, "pct_epic")
        assert prog_pre_conv.percentage == 96.0

        # Gate 4 + Review Converged -> 100.0%
        (repo / ".devtool" / "GATE_LEDGER.md").write_text(
            "| Timestamp | Epic | Gate | Commit | Approved Scope | Deviations | By |\n"
            "|---|---|---|---|---|---|---|\n"
            "| 2026-11-11T04:00:00Z | pct_epic | 4 | aaa1111 | Gate 4 PASS |  | dev |\n",
            encoding="utf-8",
        )
        (repo / ".devtool" / "assistant_state.md").write_text(
            "# Active Epic: pct_epic\n## Status:\nReview Converged\n",
            encoding="utf-8",
        )
        prog_converged = check_tasks.extract_task_progress(repo, "pct_epic")
        assert prog_converged.percentage == 100.0

    def test_legacy_pending_decision_fallback(self, tmp_path: Path) -> None:
        """Verify legacy single-record pending_decision.json fallback respects matching epic isolation."""
        repo = _init_git_repo(tmp_path / "legacy-pd-repo")
        state_dir = repo / ".devtool" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "pending_decision.json").write_text(
            json.dumps(
                {
                    "active": True,
                    "epic": "legacy-epic",
                    "reason": "Confirm legacy Gate 2 decision",
                    "stage": "Stage 2 (Architecture)",
                }
            ),
            encoding="utf-8",
        )

        assert check_tasks.resolve_active_epic(repo) == "legacy-epic"
        meta_match = check_tasks.scan_repo(repo)
        assert meta_match.is_human_action_required is True
        assert meta_match.prompt == "Confirm legacy Gate 2 decision"
        assert meta_match.pending_decision is not None
        assert meta_match.pending_decision["epic"] == "legacy-epic"

        other_dec = check_tasks.derive_lifecycle_state(repo, "other-epic")
        assert other_dec.is_human_action_required is False

