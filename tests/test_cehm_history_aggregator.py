"""Tests for CEHM Task 2: epic history aggregator, timeline stitching, and scoped API.

BDD scenarios covered:
- CEHM-HP-02: Stitch completed legacy epic history across ledger, archives, tasks, and evidence
- CEHM-HP-03: /api/epic/history multi-round principal & cross-model review retrieval
- CEHM-EC-01: Empty draft/backlog epic graceful state with zero tasks/logs/reviews
- CEHM-EC-02: Strict per-epic review scoping blocks root review leakage
- CEHM-ST-01: Timeline mirror deduplication and log_completeness fidelity calculation
- CEHM-AR-03: /api/epic/history input validation, traversal guard, and 400/404 responses
- CEHM-FR-01: Resilience to malformed JSONL event lines and corrupt evidence JSON
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import urllib.error
import urllib.request
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_tasks  # noqa: E402
import tasks_server  # noqa: E402


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: Any) -> None:
    _write_text(path, json.dumps(data, indent=2) + "\n")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def _running_server(workspace_root: Path, pid_file: Path) -> Generator[str, None, None]:
    port = _find_free_port()
    srv = tasks_server.TasksServer(
        host="127.0.0.1",
        port=port,
        workspace_root=workspace_root,
        pid_file=pid_file,
    )
    thread = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.05})
    thread.daemon = True
    thread.start()
    base_url = f"http://127.0.0.1:{srv.server_port}"
    try:
        yield base_url
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=2.0)


def _http_get_json(url: str) -> tuple[int, dict[str, Any]]:
    try:
        with urllib.request.urlopen(url, timeout=5.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return int(resp.status), dict(body)
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return int(err.code), dict(parsed)


def _test_cehm_hp_02_impl(tmp_path: Path) -> None:
    """Shared real-filesystem aggregator fixture for CEHM-HP-02."""
    repo = tmp_path / "legacy_repo"
    epic_slug = "alignment_flow_hardening"
    epic_dir = repo / ".devtool" / "epic" / epic_slug

    _write_text(
        repo / ".devtool" / "PROJECT_LEDGER.md",
        "# Project Ledger\n\n"
        "- **[2026-11-14] `alignment_flow_hardening`**: Hardened workflow alignment.\n",
    )
    _write_text(
        epic_dir / f"{epic_slug}.en.md",
        "# Epic: Alignment Flow Hardening\n\n"
        "- **Status**: Done\n"
        "- **PIC**: phungthuy8901\n",
    )
    _write_text(
        epic_dir / "task_01_alpha.md",
        "---\n"
        f"epic: {epic_slug}\n"
        "status: done\n"
        "priority: high\n"
        'labels: ["backend", "telemetry"]\n'
        "completedAt: 2026-11-14T12:00:00Z\n"
        "---\n\n"
        "# Task 1: Alpha Hardening\n",
    )
    _write_json(
        epic_dir / "evidence" / "task_01_alpha.json",
        {
            "task": "task_01_alpha",
            "status": "done",
            "runs": {
                "verify": {
                    "head": "abc123def456",
                    "started": "2026-11-14T11:55:00Z",
                    "finished": "2026-11-14T11:56:00Z",
                    "rows": [
                        {
                            "id": "V1",
                            "phase": "verify",
                            "command": "pytest tests/test_alpha.py",
                            "outcome": "PASS",
                            "output_tail": [f"log line {i}" for i in range(15)],
                            "reason": "",
                        }
                    ],
                }
            },
        },
    )
    _write_json(
        repo / ".devtool" / "state" / "alignment-flow-hardening.heartbeat.json",
        {
            "generation": 4,
            "epic_slug": epic_slug,
            "stage": "finish",
            "updated_at": "2026-11-14T12:05:00Z",
            "events": [
                {
                    "ts": "2026-11-14T11:45:00Z",
                    "stage": "tasks",
                    "sub_step": "wave_1",
                    "message": "Task 01 started",
                },
                {
                    "ts": "2026-11-14T12:05:00Z",
                    "stage": "finish",
                    "sub_step": "gate_5",
                    "message": "Merged & archived",
                },
            ],
        },
    )
    _write_json(
        repo
        / ".devtool"
        / "archive"
        / "heartbeat_alignment_flow_hardening_20261114_1200.json",
        {
            "generation": 2,
            "epic_slug": epic_slug,
            "stage": "hld_principal",
            "updated_at": "2026-11-14T11:45:00Z",
            "events": [
                {
                    "ts": "2026-11-14T11:30:00Z",
                    "stage": "hld_principal",
                    "sub_step": "hld_ready",
                    "message": "Packaged epic tasks",
                },
                {
                    "ts": "2026-11-14T11:45:00Z",
                    "stage": "tasks",
                    "sub_step": "wave_1",
                    "message": "Task 01 started",
                },
            ],
        },
    )
    _write_text(
        repo / ".devtool" / "state" / "gate_ledger.jsonl",
        json.dumps(
            {
                "gate": 1,
                "epic": epic_slug,
                "timestamp": "2026-11-14T10:00:00Z",
                "approver": "Human Architect",
                "summary": "Spec approved",
            }
        )
        + "\n"
        + json.dumps(
            {
                "gate": 4,
                "epic": epic_slug,
                "timestamp": "2026-11-14T11:58:00Z",
                "by": "Quality Gatekeeper",
                "commit": "abc123def456",
                "approved": "Gate 4 QA PASS",
            }
        )
        + "\n"
        + json.dumps(
            {
                "gate": 5,
                "epic": epic_slug,
                "timestamp": "2026-11-14T12:10:00Z",
                "approver": "Human Architect",
                "summary": "Merged & Archived",
            }
        )
        + "\n",
    )
    _write_text(
        repo
        / ".devtool"
        / "archive"
        / "activity_alignment_flow_hardening_20261114_1200.log",
        "# Archived Activity Log\n"
        "- [2026-11-14 11:50] Verified alpha hardening checks\n",
    )

    assert set(check_tasks._collect_slug_variants(epic_slug)) == {
        "alignment_flow_hardening",
        "alignment-flow-hardening",
    }

    history = check_tasks.harvest_epic_history(repo, epic_slug)
    assert history["epic"]["slug"] == epic_slug
    assert history["epic"]["status"] == "done"
    assert history["epic"]["title"] == "Alignment Flow Hardening"
    assert history["epic"]["pic"] == "phungthuy8901"

    telemetry = history["pipeline_telemetry"]
    assert len(telemetry["stages"]) == 6
    assert telemetry["stages"][5]["status"] == "done"
    assert telemetry["lifecycle_progress_pct"] == 100.0

    assert len(history["tasks"]) == 1
    task = history["tasks"][0]
    assert task["id"] == "task_01_alpha"
    assert task["status"] == "done"
    assert task["evidence"] is not None
    assert task["evidence"]["passed_rows"] == 1
    assert task["evidence"]["total_rows"] == 1
    assert task["evidence"]["head"] == "abc123def456"
    assert len(task["evidence"]["rows"][0]["output_tail"]) <= 8

    timeline = history["timeline"]
    categories = {item["category"] for item in timeline}
    assert {"gate", "step", "activity", "evidence"}.issubset(categories)
    gate_items = [item for item in timeline if item["category"] == "gate"]
    gate4_item = next(item for item in gate_items if item["sub_step"] == "gate_4")
    assert gate4_item["message"] == "Gate 4: Gate 4 QA PASS"
    assert gate4_item["detail"] == "Quality Gatekeeper (abc123def456)"
    step_msgs = [item["message"] for item in timeline if item["category"] == "step"]
    assert step_msgs.count("Task 01 started") == 1
    timestamps = [item["ts"] for item in timeline]
    assert timestamps == sorted(timestamps)

    # Guardrail: /api/tasks active task polling still skips legacy completed epics.
    active_tp = check_tasks.extract_task_progress(repo, None)
    assert all(t["id"] != "task_01_alpha" for t in active_tp.tasks)


def test_cehm_hp_02_stitch_legacy_done_epic(tmp_path: Path) -> None:
    """CEHM-HP-02: Stitch legacy Done epic across ledger, archives, tasks, and bounded evidence."""
    _test_cehm_hp_02_impl(tmp_path)


class TestCehm_Integration:
    """Tier C integration runner exercising real filesystem & live HTTP TasksServer."""

    def test_cehm_hp_02_stitch_legacy_done_epic(self, tmp_path: Path) -> None:
        """CEHM-HP-02: Tier C integration provenance for legacy Done epic stitching."""
        _test_cehm_hp_02_impl(tmp_path)

    def test_cehm_hp_03_history_endpoint_multi_round_reviews(
        self, tmp_path: Path
    ) -> None:
        """CEHM-HP-03: /api/epic/history selects requested principal and cross-model rounds."""
        ws = tmp_path / "ws"
        repo = ws / "demo_repo"
        epic_slug = "hist_epic"
        epic_dir = repo / ".devtool" / "epic" / epic_slug

        _write_text(
            epic_dir / f"{epic_slug}.en.md",
            "# Epic: History Endpoint Epic\n\n- **Status**: In Progress\n",
        )
        _write_text(
            repo / ".devtool" / "features" / "task_01_api.md",
            "---\n"
            f"epic: {epic_slug}\n"
            "status: done\n"
            "---\n\n"
            "# Task 1: History Endpoint\n",
        )
        _write_text(
            epic_dir / "principal_review.md",
            "# Principal Review\n\n"
            "## Round 1\n"
            "- **Overall Verdict**: 🔴 REVISE\n"
            "- **Reviewer / Provider**: claude\n"
            "| # | Severity | Location | Problem | Decision |\n"
            "|---|---|---|---|---|\n"
            "| PR-1 | Important | HLD | Missing timeout note | Fixed |\n\n"
            "## Round 2\n"
            "- **Overall Verdict**: 🟢 LGTM\n"
            "- **Candidate Commit SHA**: deadbeef\n"
            "- **Reviewer / Provider**: claude\n"
            "| # | Severity | Location | Problem | Decision |\n"
            "|---|---|---|---|---|\n",
        )
        _write_text(
            epic_dir / "review_results.md",
            "# Cross-Model Review\n\n"
            "## Round 1\n"
            "- **Overall Verdict**: 🟡 CONCERNS\n"
            "- **Candidate Commit SHA**: cafe1234\n"
            "- **Reviewer / Provider**: codex\n"
            "| # | Severity | Location | Problem | Decision |\n"
            "|---|---|---|---|---|\n"
            "| CM-1 | Minor | tasks_server.py | Add doc note | Pending |\n",
        )

        # Per-round-only files with omitted round_* query params (target_round=None)
        per_round_dir = repo / ".devtool" / "epic" / "per_round_epic"
        _write_text(
            per_round_dir / "per_round_epic.en.md",
            "# Epic: Per Round Only Epic\n\n- **Status**: In Progress\n",
        )
        _write_text(
            per_round_dir / "principal_review_round_1.md",
            "# Principal Review\n\n- **Overall Verdict**: 🟢 LGTM\n",
        )
        _write_text(
            per_round_dir / "review_results_round_2.md",
            "# Cross-Model Review\n\n"
            "- **Overall Verdict**: 🟡 CONCERNS\n"
            "| # | Severity | Location | Problem | Decision |\n"
            "|---|---|---|---|---|\n"
            "| R2-1 | Minor | check_tasks.py | Check edge | Pending |\n",
        )

        # Mixed unnumbered + per-round review files
        mixed_dir = repo / ".devtool" / "epic" / "mixed_epic"
        _write_text(
            mixed_dir / "mixed_epic.en.md",
            "# Epic: Mixed Rounds Epic\n\n- **Status**: In Progress\n",
        )
        _write_text(
            mixed_dir / "principal_review.md",
            "# Principal Review\n\n## Round 1\n- **Overall Verdict**: 🔴 REVISE\n",
        )
        _write_text(
            mixed_dir / "principal_review_round_2.md",
            "# Principal Review Round 2\n\n- **Overall Verdict**: 🟢 LGTM\n",
        )

        with _running_server(ws, tmp_path / "tasks.pid") as base_url:
            status, payload = _http_get_json(
                f"{base_url}/api/epic/history"
                "?repo=demo_repo&epic=hist_epic&round_principal=2&round_cross=1"
            )
            st_pr, pl_pr = _http_get_json(
                f"{base_url}/api/epic/history?repo=demo_repo&epic=per_round_epic"
            )
            st_mx1, pl_mx1 = _http_get_json(
                f"{base_url}/api/epic/history?repo=demo_repo&epic=mixed_epic"
            )
            st_mx2, pl_mx2 = _http_get_json(
                f"{base_url}/api/epic/history"
                "?repo=demo_repo&epic=mixed_epic&round_principal=2"
            )

        assert status == 200
        assert payload["success"] is True
        assert payload["epic"]["slug"] == epic_slug
        assert len(payload["pipeline_telemetry"]["stages"]) == 6
        assert len(payload["tasks"]) == 1

        pr = payload["reviews"]["principal"]
        cm = payload["reviews"]["cross_model"]
        assert pr["present"] is True
        assert pr["round"] == 2
        assert pr["available_rounds"] == [1, 2]
        assert "LGTM" in pr["verdict"]
        assert cm["present"] is True
        assert cm["round"] == 1
        assert len(cm["findings"]) == 1
        assert cm["findings"][0]["id"] == "CM-1"

        assert st_pr == 200
        assert pl_pr["reviews"]["principal"]["present"] is True
        assert pl_pr["reviews"]["principal"]["round"] == 1
        assert pl_pr["reviews"]["principal"]["available_rounds"] == [1]
        assert pl_pr["reviews"]["cross_model"]["present"] is True
        assert pl_pr["reviews"]["cross_model"]["round"] == 2
        assert pl_pr["reviews"]["cross_model"]["available_rounds"] == [2]
        assert len(pl_pr["reviews"]["cross_model"]["findings"]) == 1

        assert st_mx1 == 200
        assert pl_mx1["reviews"]["principal"]["round"] == 1
        assert pl_mx1["reviews"]["principal"]["available_rounds"] == [1, 2]
        assert st_mx2 == 200
        assert pl_mx2["reviews"]["principal"]["round"] == 2
        assert pl_mx2["reviews"]["principal"]["available_rounds"] == [1, 2]
        assert "LGTM" in pl_mx2["reviews"]["principal"]["verdict"]

    def test_cehm_ar_03_history_endpoint_validation_and_traversal(
        self, tmp_path: Path
    ) -> None:
        """CEHM-AR-03: /api/epic/history rejects missing params, traversal, and unknown targets."""
        ws = tmp_path / "ws"
        repo = ws / "demo_repo"
        _write_text(
            repo / ".devtool" / "epic" / "hist_epic" / "hist_epic.en.md",
            "# Epic: Valid Epic\n\n- **Status**: Draft\n",
        )
        _write_text(
            repo / ".devtool" / "logs" / "activity.log",
            "- [2026-11-14 10:00] auth_refactor: touched login handler\n",
        )
        secret_file = tmp_path / "secret.txt"
        _write_text(secret_file, "TOP_SECRET_OUTSIDE_WS\n")

        with _running_server(ws, tmp_path / "tasks.pid") as base_url:
            cases = [
                f"{base_url}/api/epic/history?repo=demo_repo",
                f"{base_url}/api/epic/history?epic=hist_epic",
                f"{base_url}/api/epic/history?repo=../etc&epic=passwd",
                f"{base_url}/api/epic/history?repo=demo_repo&epic=../../secret",
                f"{base_url}/api/epic/history?repo=.&epic=hist_epic",
                f"{base_url}/api/epic/history?repo=demo_repo&epic=bad/slug",
                f"{base_url}/api/epic/history?repo=missing_repo&epic=bad/slug",
            ]
            for url in cases:
                code, payload = _http_get_json(url)
                assert code == 400, f"Expected 400 for {url}, got {code}: {payload}"
                assert payload["success"] is False
                assert "TOP_SECRET_OUTSIDE_WS" not in json.dumps(payload)

            code_repo, payload_repo = _http_get_json(
                f"{base_url}/api/epic/history?repo=missing_repo&epic=hist_epic"
            )
            assert code_repo == 404
            assert payload_repo["success"] is False

            code_epic, payload_epic = _http_get_json(
                f"{base_url}/api/epic/history?repo=demo_repo&epic=does_not_exist"
            )
            assert code_epic == 404
            assert payload_epic["success"] is False

            # Partial prefix in shared activity.log must NOT make unknown 'auth' exist.
            code_prefix, payload_prefix = _http_get_json(
                f"{base_url}/api/epic/history?repo=demo_repo&epic=auth"
            )
            assert code_prefix == 404
            assert payload_prefix["success"] is False


def test_cehm_ec_01_draft_backlog_empty_history(tmp_path: Path) -> None:
    """CEHM-EC-01: Draft/backlog epic with only design spec returns valid empty payload."""
    ws = tmp_path / "ws"
    repo = ws / "demo_repo"
    epic_slug = "draft_epic"
    _write_text(
        repo / ".devtool" / "epic" / epic_slug / "2026-11-15-draft-epic-design.en.md",
        "# Draft Epic Design\n\n- **Status**: Draft\n",
    )

    with _running_server(ws, tmp_path / "tasks.pid") as base_url:
        status, payload = _http_get_json(
            f"{base_url}/api/epic/history?repo=demo_repo&epic=draft_epic"
        )

    assert status == 200
    assert payload["success"] is True
    assert payload["epic"]["slug"] == epic_slug
    assert payload["tasks"] == []
    assert payload["timeline"] == []
    assert payload["log_completeness"] == "none"
    assert len(payload["pipeline_telemetry"]["stages"]) == 6
    assert payload["reviews"]["principal"]["present"] is False
    assert payload["reviews"]["cross_model"]["present"] is False


def test_cehm_ec_02_strict_epic_review_isolation(tmp_path: Path) -> None:
    """CEHM-EC-02: strict_epic=True prevents repo-root review files leaking into old epics."""
    ws = tmp_path / "ws"
    repo = ws / "demo_repo"
    _write_text(
        repo / ".devtool" / "epic" / "legacy_oct_epic" / "legacy_oct_epic.en.md",
        "# Epic: Legacy Oct Epic\n\n- **Status**: Done\n",
    )
    _write_text(
        repo / ".devtool" / "principal_review.md",
        "# Principal Review\n\n## Round 1\n- **Overall Verdict**: 🟢 LGTM\n",
    )
    _write_text(
        repo / ".devtool" / "review_results.md",
        "# Cross-Model Review\n\n"
        "## Round 1\n"
        "- **Overall Verdict**: 🔴 BLOCKED\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|---|---|---|---|\n"
        "| X-1 | Critical | root.py | Root bug from active epic | Open |\n",
    )

    strict_pr = tasks_server.parse_review_results(
        repo, active_epic="legacy_oct_epic", kind="principal", strict_epic=True
    )
    strict_cm = tasks_server.parse_review_results(
        repo, active_epic="legacy_oct_epic", kind="cross-model", strict_epic=True
    )
    assert strict_pr["present"] is False
    assert strict_pr["verdict"] == "UNKNOWN"
    assert strict_pr["findings"] == []
    assert strict_cm["present"] is False
    assert strict_cm["verdict"] == "UNKNOWN"
    assert strict_cm["findings"] == []

    # Backward compatibility: default strict_epic=False keeps legacy root fallback.
    compat_cm = tasks_server.parse_review_results(
        repo, active_epic="legacy_oct_epic", kind="cross-model"
    )
    assert compat_cm["present"] is True
    assert len(compat_cm["findings"]) == 1

    with _running_server(ws, tmp_path / "tasks.pid") as base_url:
        status, payload = _http_get_json(
            f"{base_url}/api/epic/history?repo=demo_repo&epic=legacy_oct_epic"
        )
    assert status == 200
    assert payload["reviews"]["principal"]["present"] is False
    assert payload["reviews"]["cross_model"]["present"] is False
    assert payload["reviews"]["cross_model"]["findings"] == []


def test_cehm_st_01_timeline_dedup_and_log_completeness(tmp_path: Path) -> None:
    """CEHM-ST-01: Timeline deduplicates mirrors & heartbeats and tracks log_completeness."""
    repo = tmp_path / "stream_repo"

    # Full stream case: 10 archived + 12 active events = 22 unique steps, plus mirrors & heartbeats.
    arch_lines = [
        json.dumps(
            {
                "ts": f"2026-11-14T10:{i:02d}:00Z",
                "epic": "stream_epic",
                "stage": "hld_principal",
                "sub_step": f"step_{i}",
                "message": f"Archived step {i}",
            }
        )
        for i in range(10)
    ]
    _write_text(
        repo / ".devtool" / "archive" / "events_stream-epic_20261114_1200.jsonl",
        "\n".join(arch_lines) + "\n",
    )
    # Prefix-trap sibling epic MUST NOT leak into stream_epic!
    _write_text(
        repo / ".devtool" / "logs" / "events_stream_epic_v2.jsonl",
        json.dumps(
            {
                "ts": "2026-11-14T10:30:00Z",
                "epic": "stream_epic_v2",
                "stage": "tasks",
                "sub_step": "v2",
                "message": "Sibling v2 event",
            }
        )
        + "\n",
    )

    active_lines = [
        json.dumps(
            {
                "ts": f"2026-11-14T11:{i:02d}:00.250000Z"
                if i == 0
                else f"2026-11-14T11:{i:02d}:00Z",
                "epic": "stream_epic",
                "stage": "tasks",
                "sub_step": f"active_{i}",
                "message": f"Active step {i}",
            }
        )
        for i in range(12)
    ]
    active_content = "\n".join(active_lines) + "\n"
    _write_text(repo / ".devtool" / "logs" / "events_stream_epic.jsonl", active_content)
    # Linked worktree mirror writes identical active lines: must dedup cleanly.
    _write_text(
        repo
        / ".worktrees"
        / "stream_epic"
        / ".devtool"
        / "logs"
        / "events_stream_epic.jsonl",
        active_content,
    )
    # Heartbeat holds trailing 8 events (including an idle-tick timestamp-shifted duplicate).
    hb_events = [json.loads(line) for line in active_lines[-8:]]
    hb_events[-1]["ts"] = "2026-11-14T11:59:00Z"
    _write_json(
        repo / ".devtool" / "state" / "stream-epic.heartbeat.json",
        {
            "generation": 5,
            "epic_slug": "stream_epic",
            "stage": "tasks",
            "updated_at": "2026-11-14T11:59:00Z",
            "events": hb_events,
        },
    )

    _write_text(
        repo / ".devtool" / "logs" / "activity.log",
        "- [2026-11-14 11:55] [stream_epic] Valid shared activity\n"
        "- [2026-11-14 11:56] [stream_epic_v2] Sibling shared activity\n"
        "- [2026-11-14 11:57] auth_refactor: partial prefix activity\n",
    )

    stream_hist = check_tasks.harvest_epic_history(repo, "stream_epic")
    assert stream_hist["log_completeness"] == "full_stream"
    step_events = [e for e in stream_hist["timeline"] if e["category"] == "step"]
    assert len(step_events) == 22
    assert all("Sibling v2 event" not in e["message"] for e in step_events)
    act_msgs = [
        e["message"] for e in stream_hist["timeline"] if e["category"] == "activity"
    ]
    assert act_msgs == ["[stream_epic] Valid shared activity"]
    assert check_tasks.harvest_epic_history(repo, "auth")["exists"] is False

    # Snapshot + ledger only case: no events_*.jsonl exists for snap_epic.
    _write_text(
        repo / ".devtool" / "epic" / "snap_epic" / "snap_epic.en.md",
        "# Epic: Snapshot Epic\n\n- **Status**: In Progress\n",
    )
    _write_json(
        repo / ".devtool" / "state" / "snap_epic.heartbeat.json",
        {
            "generation": 1,
            "epic_slug": "snap_epic",
            "stage": "tasks",
            "updated_at": "2026-11-14T12:03:00Z",
            "events": [
                {
                    "ts": "2026-11-14T12:01:00.500000Z",
                    "stage": "tasks",
                    "sub_step": "wave_1",
                    "message": "Snap step 1",
                },
                {
                    "ts": "2026-11-14T12:02:00Z",
                    "stage": "tasks",
                    "sub_step": "wave_1",
                    "message": "Snap step 2",
                },
                {
                    "ts": "2026-11-14T12:03:00Z",
                    "stage": "tasks",
                    "sub_step": "wave_1",
                    "message": "Snap step 3",
                },
            ],
        },
    )
    _write_text(
        repo / ".devtool" / "state" / "gate_ledger.jsonl",
        json.dumps(
            {
                "gate": 2,
                "epic": "snap_epic",
                "timestamp": "2026-11-14T12:00:00Z",
                "approver": "Human Architect",
                "summary": "Gate 2 PASS",
            }
        )
        + "\n",
    )

    snap_hist = check_tasks.harvest_epic_history(repo, "snap_epic")
    assert snap_hist["log_completeness"] == "snapshot_and_ledger"
    assert len(snap_hist["timeline"]) == 4


def test_cehm_fr_01_malformed_jsonl_and_corrupt_evidence(tmp_path: Path) -> None:
    """CEHM-FR-01: Malformed JSONL lines and corrupt evidence JSON degrade cleanly."""
    ws = tmp_path / "ws"
    repo = ws / "fragile_repo"
    epic_slug = "corrupt-epic"
    epic_dir = repo / ".devtool" / "epic" / epic_slug

    _write_text(
        epic_dir / f"{epic_slug}.en.md",
        "# Epic: Corrupt Resilient Epic\n\n- **Status**: In Progress\n",
    )
    _write_text(
        repo / ".devtool" / "logs" / f"events_{epic_slug}.jsonl",
        json.dumps(
            {
                "ts": "2026-11-14T09:00:00Z",
                "epic": epic_slug,
                "stage": "tasks",
                "sub_step": "wave_1",
                "message": "Valid first line",
            }
        )
        + '\n\n{bad json line\n"just-a-string"\n'
        + json.dumps(
            {
                "ts": "2026-11-14T09:05:00Z",
                "epic": epic_slug,
                "stage": "tasks",
                "sub_step": "wave_1",
                "message": "Valid second line",
            }
        )
        + "\n",
    )
    _write_text(
        repo / ".devtool" / "archive" / "heartbeat_corrupt-epic_20261114_1200.json",
        "{corrupt archived heartbeat",
    )
    _write_text(
        repo / ".devtool" / "features" / "task_01_broken.md",
        f"---\nepic: {epic_slug}\nstatus: done\n---\n\n# Task 1: Broken Evidence\n",
    )
    _write_text(epic_dir / "evidence" / "task_01_broken.json", "{not valid json")

    history = check_tasks.harvest_epic_history(repo, epic_slug)
    assert history["log_completeness"] == "full_stream"
    step_msgs = [
        item["message"] for item in history["timeline"] if item["category"] == "step"
    ]
    assert step_msgs == ["Valid first line", "Valid second line"]
    assert len(history["tasks"]) == 1
    assert history["tasks"][0]["id"] == "task_01_broken"
    assert history["tasks"][0]["evidence"] is None

    with _running_server(ws, tmp_path / "tasks.pid") as base_url:
        status, payload = _http_get_json(
            f"{base_url}/api/epic/history?repo=fragile_repo&epic={epic_slug}"
        )
    assert status == 200
    assert payload["success"] is True
    assert payload["tasks"][0]["evidence"] is None


def test_cehm_regression_round1_review_transition_deduplication(
    tmp_path: Path,
) -> None:
    """Regression #1: Deduplication must preserve distinct review transitions sharing timestamp, stage, sub_step, and message."""
    repo = tmp_path / "dedup_repo"
    epic_slug = "review_dedup_epic"
    epic_dir = repo / ".devtool" / "epic" / epic_slug
    _write_text(
        epic_dir / f"{epic_slug}.en.md",
        "# Epic: Review Dedup Epic\n\n- **Status**: In Progress\n",
    )
    ev1 = {
        "ts": "2026-11-14T21:00:00Z",
        "epic": epic_slug,
        "stage": "Stage 5",
        "sub_step": "review",
        "message": "cross-model review",
        "review_state": {
            "kind": "code",
            "round": 1,
            "phase": "reviewing",
            "cli": "codex",
        },
    }
    ev2 = {
        "ts": "2026-11-14T21:00:00Z",
        "epic": epic_slug,
        "stage": "Stage 5",
        "sub_step": "review",
        "message": "cross-model review",
        "review_state": {
            "kind": "code",
            "round": 1,
            "phase": "triage",
            "action": "AUTO_FIX_ELIGIBLE",
        },
    }
    stream_file = repo / ".devtool" / "logs" / f"events_{epic_slug}.jsonl"
    _write_text(stream_file, json.dumps(ev1) + "\n" + json.dumps(ev2) + "\n")

    merged = check_tasks._merge_epic_heartbeats(repo, epic_slug)
    assert len(merged["step_events"]) == 2
    assert merged["step_events"][0]["review_state"]["phase"] == "reviewing"
    assert merged["step_events"][1]["review_state"]["phase"] == "triage"

    history = check_tasks.harvest_epic_history(repo, epic_slug)
    timeline_steps = [ev for ev in history["timeline"] if ev.get("category") == "step"]
    assert len(timeline_steps) == 2
    assert timeline_steps[0]["review_state"]["phase"] == "reviewing"
    assert timeline_steps[1]["review_state"]["phase"] == "triage"


def test_cehm_regression_round1_packaged_hld_with_gate2_status(
    tmp_path: Path,
) -> None:
    """Regression #2: A Packaged HLD with Gate 2 in ledger must stay 'packaged' and not become 'in_progress'."""
    repo = tmp_path / "packaged_repo"
    epic_slug = "packaged_sample_epic"
    epic_dir = repo / ".devtool" / "epic" / epic_slug
    _write_text(
        epic_dir / f"{epic_slug}.en.md",
        "---\nstatus: packaged\n---\n\n# Epic: Packaged Sample\n\n- **Status**: Packaged\n",
    )
    ledger = (
        "# Gate Ledger\n\n"
        f"| 2026-11-14T10:00:00Z | {epic_slug} | 1 | Architect | a1b2c3d | Gate 1 Inception |\n"
        f"| 2026-11-14T11:00:00Z | {epic_slug} | 2 | Architect | d4e5f6a | Gate 2 Packaging |\n"
    )
    _write_text(repo / ".devtool" / "GATE_LEDGER.md", ledger)

    history = check_tasks.harvest_epic_history(repo, epic_slug)
    assert history["epic"]["status"] == "packaged"

    meta = check_tasks.scan_repo(repo)
    assert meta.epics_summary is not None
    matching = [e for e in meta.epics_summary.epics if e.get("slug") == epic_slug]
    assert len(matching) == 1
    assert matching[0]["status"] == "packaged"


def test_cehm_regression_round1_unreadable_review_files_resilience(
    tmp_path: Path,
) -> None:
    """Regression #3: Unreadable / non-UTF-8 review files must not abort /api/epic/history."""
    ws = tmp_path / "resilient_ws"
    repo = ws / "corrupt_rev_repo"
    epic_slug = "corrupt_rev_epic"
    epic_dir = repo / ".devtool" / "epic" / epic_slug

    _write_text(
        epic_dir / f"{epic_slug}.en.md",
        "# Epic: Corrupt Review Resilience\n\n- **Status**: In Progress\n",
    )
    _write_text(
        repo / ".devtool" / "features" / "task_01_core.md",
        f"---\nepic: {epic_slug}\nstatus: done\n---\n\n# Task 1: Core Function\n",
    )
    _write_text(
        repo / ".devtool" / "logs" / f"events_{epic_slug}.jsonl",
        json.dumps(
            {
                "ts": "2026-11-14T20:00:00Z",
                "epic": epic_slug,
                "stage": "tasks",
                "sub_step": "coding",
                "message": "Valid task timeline",
            }
        )
        + "\n",
    )
    bad_bytes = b"\x80\xff\xfe\x00corrupt-bytes"
    rev_file = epic_dir / "review_results.md"
    rev_file.parent.mkdir(parents=True, exist_ok=True)
    rev_file.write_bytes(bad_bytes)
    pr_file = epic_dir / "principal_review.md"
    pr_file.write_bytes(bad_bytes)

    with _running_server(ws, tmp_path / "tasks.pid") as base_url:
        status, payload = _http_get_json(
            f"{base_url}/api/epic/history?repo=corrupt_rev_repo&epic={epic_slug}"
        )

    assert status == 200
    assert payload["success"] is True
    assert len(payload["tasks"]) == 1
    assert payload["tasks"][0]["id"] == "task_01_core"
    assert len(payload["timeline"]) >= 1
    assert payload["reviews"]["principal"]["present"] is False
    assert payload["reviews"]["cross_model"]["present"] is False


@pytest.mark.parametrize(
    ("stream_same_ts", "hb_shift_ts"),
    [
        (True, False),  # Identical timestamps across stream transitions and heartbeat
        (False, False),  # Sequential timestamps across stream transitions
        (True, True),  # Shifted timestamp on heartbeat (idle tick)
        (False, True),  # Sequential timestamps + shifted heartbeat
    ],
)
def test_cehm_regression_round2_review_heartbeat_overlap_deduplication(
    tmp_path: Path,
    stream_same_ts: bool,
    hb_shift_ts: bool,
) -> None:
    """Regression #1 (Round 2): Overlapping heartbeat omitting review_state must deduplicate against stream."""
    repo = tmp_path / f"dedup_repo_{stream_same_ts}_{hb_shift_ts}"
    epic_slug = "review_dedup_r2"
    epic_dir = repo / ".devtool" / "epic" / epic_slug
    _write_text(
        epic_dir / f"{epic_slug}.en.md",
        "# Epic: Review Dedup Epic R2\n\n- **Status**: In Progress\n",
    )

    ts1 = "2026-11-14T21:00:00Z"
    ts2 = "2026-11-14T21:00:00Z" if stream_same_ts else "2026-11-14T21:00:05Z"
    ts_hb = "2026-11-14T21:00:10Z" if hb_shift_ts else ts2

    ev1 = {
        "ts": ts1,
        "epic": epic_slug,
        "stage": "Stage 5",
        "sub_step": "review",
        "message": "cross-model review",
        "review_state": {
            "kind": "code",
            "round": 1,
            "phase": "reviewing",
            "cli": "codex",
        },
    }
    ev2 = {
        "ts": ts2,
        "epic": epic_slug,
        "stage": "Stage 5",
        "sub_step": "review",
        "message": "cross-model review",
        "review_state": {
            "kind": "code",
            "round": 1,
            "phase": "triage",
            "action": "AUTO_FIX_ELIGIBLE",
        },
    }
    stream_file = repo / ".devtool" / "logs" / f"events_{epic_slug}.jsonl"
    _write_text(stream_file, json.dumps(ev1) + "\n" + json.dumps(ev2) + "\n")

    # Production heartbeat events ring buffer omits review_state
    hb_item = {
        "ts": ts_hb,
        "stage": "Stage 5",
        "sub_step": "review",
        "message": "cross-model review",
    }
    _write_json(
        repo / ".devtool" / "state" / f"{epic_slug}.heartbeat.json",
        {
            "generation": 1,
            "epic_slug": epic_slug,
            "stage": "Stage 5",
            "sub_step": "review",
            "updated_at": ts_hb,
            "events": [hb_item],
        },
    )

    merged = check_tasks._merge_epic_heartbeats(repo, epic_slug)
    # Must contain exactly 2 events (the two stream transitions), NOT 3!
    assert len(merged["step_events"]) == 2
    assert merged["step_events"][0]["review_state"]["phase"] == "reviewing"
    assert merged["step_events"][1]["review_state"]["phase"] == "triage"

    history = check_tasks.harvest_epic_history(repo, epic_slug)
    timeline_steps = [ev for ev in history["timeline"] if ev.get("category") == "step"]
    assert len(timeline_steps) == 2
    assert timeline_steps[0]["review_state"]["phase"] == "reviewing"
    assert timeline_steps[1]["review_state"]["phase"] == "triage"


def test_cehm_regression_round2_unified_timeline_ordering_and_tie_breaking(
    tmp_path: Path,
) -> None:
    """Regression #1 order-invariance: If heartbeat empty review_state precedes stream, stream still wins."""
    repo = tmp_path / "order_repo"
    raw_step_events: list[dict[str, Any]] = [
        # Heartbeat event (omits review_state) comes FIRST
        {
            "ts": "2026-11-14T21:00:00Z",
            "category": "step",
            "stage": "Stage 5",
            "sub_step": "review",
            "message": "cross-model review",
            "source": "heartbeat",
        },
        # Followed by stream event 1
        {
            "ts": "2026-11-14T21:00:00Z",
            "category": "step",
            "stage": "Stage 5",
            "sub_step": "review",
            "message": "cross-model review",
            "source": "stream",
            "review_state": {"phase": "reviewing"},
        },
        # And stream event 2
        {
            "ts": "2026-11-14T21:00:00Z",
            "category": "step",
            "stage": "Stage 5",
            "sub_step": "review",
            "message": "cross-model review",
            "source": "stream",
            "review_state": {"phase": "triage"},
        },
    ]
    timeline = check_tasks._build_unified_timeline(
        repo, "test_epic", raw_step_events, [], [], []
    )
    assert len(timeline) == 2
    phases = [ev["review_state"]["phase"] for ev in timeline]
    assert "reviewing" in phases
    assert "triage" in phases


@pytest.mark.parametrize(
    (
        "variant_name",
        "has_gate3",
        "has_wt",
        "has_active_task",
        "has_active_telemetry",
        "expected_status",
    ),
    [
        ("gate1_gate2_only", False, False, False, False, "packaged"),
        ("gate3_approved_no_wt", True, False, False, False, "in_progress"),
        ("worktree_present", False, True, False, False, "in_progress"),
        ("active_task_present", False, False, True, False, "in_progress"),
        ("active_telemetry_hb", False, False, False, True, "in_progress"),
    ],
)
def test_cehm_regression_round2_packaged_hld_roadmap_and_history_parity(
    tmp_path: Path,
    variant_name: str,
    has_gate3: bool,
    has_wt: bool,
    has_active_task: bool,
    has_active_telemetry: bool,
    expected_status: str,
) -> None:
    """Regression #2 (Round 2): Packaged HLD parity across scan_repo (Roadmap) and harvest_epic_history (History)."""
    repo = tmp_path / f"parity_repo_{variant_name}"
    epic_slug = f"parity_epic_{variant_name}"
    epic_dir = repo / ".devtool" / "epic" / epic_slug
    _write_text(
        epic_dir / f"{epic_slug}.en.md",
        f"---\nstatus: packaged\n---\n\n# Epic: Parity {variant_name}\n\n- **Status**: Packaged\n",
    )

    # Base ledger: Gate 1 and Gate 2
    ledger_lines = [
        "# Gate Ledger\n",
        f"| 2026-11-14T10:00:00Z | {epic_slug} | 1 | Architect | a1b2c3d | Gate 1 Inception |",
        f"| 2026-11-14T11:00:00Z | {epic_slug} | 2 | Architect | d4e5f6a | Gate 2 Packaging |",
    ]
    if has_gate3:
        ledger_lines.append(
            f"| 2026-11-14T12:00:00Z | {epic_slug} | 3 | Architect | g7h8i9j | Gate 3 Approved |"
        )
    _write_text(repo / ".devtool" / "GATE_LEDGER.md", "\n".join(ledger_lines) + "\n")

    if has_wt:
        (repo / ".worktrees" / epic_slug).mkdir(parents=True, exist_ok=True)

    if has_active_task:
        _write_text(
            epic_dir / "task_01_core.md",
            f"---\nepic: {epic_slug}\nstatus: in-progress\n---\n\n# Task 1\n",
        )
    else:
        # Idle task in todo state
        _write_text(
            epic_dir / "task_01_core.md",
            f"---\nepic: {epic_slug}\nstatus: todo\n---\n\n# Task 1\n",
        )

    if has_active_telemetry:
        _write_json(
            repo / ".devtool" / "state" / f"{epic_slug}.heartbeat.json",
            {
                "generation": 1,
                "epic_slug": epic_slug,
                "stage": "tasks",
                "sub_step": "coding",
                "updated_at": "2026-11-14T12:30:00Z",
                "events": [
                    {
                        "ts": "2026-11-14T12:30:00Z",
                        "stage": "tasks",
                        "sub_step": "coding",
                        "message": "Active coding task",
                    }
                ],
            },
        )

    # Verify History modal status
    history = check_tasks.harvest_epic_history(repo, epic_slug)
    assert history["epic"]["status"] == expected_status, (
        f"History status mismatch for {variant_name}: expected {expected_status}, got {history['epic']['status']}"
    )

    # Verify Roadmap (scan_repo) status
    meta = check_tasks.scan_repo(repo)
    assert meta.epics_summary is not None
    matching = [e for e in meta.epics_summary.epics if e.get("slug") == epic_slug]
    assert len(matching) == 1
    assert matching[0]["status"] == expected_status, (
        f"Roadmap status mismatch for {variant_name}: expected {expected_status}, got {matching[0]['status']}"
    )
