"""End-to-end integration and headless Chrome CDP acceptance test suite for
lifecycle_telemetry_and_stage_progress_ui.

Covers BDD Scenarios:
- LTSP-HP-06: End-to-end headless Chrome CDP verifies live stage and micro-step transitions from Tasks to Quality Check to Cross-Model Review
- LTSP-EC-04: Expandable event log drawer preserves expanded state across live pollDashboard ticks
- LTSP-ST-04: Commit-based fix and verification detection infers fixing after commit and verifying only when verification executes
- LTSP-AR-03: Multi-epic workspace isolates pipeline_telemetry per epic across active and secondary in-progress epics
- LTSP-FR-03: Corrupted or truncated review_results.md / heartbeat.json files recover cleanly during pipeline harvesting
"""

from __future__ import annotations

import http.server
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
CHECK_TASKS_DIR = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
DASHBOARD_HTML = (
    REPO_ROOT
    / "skills"
    / "check-tasks"
    / "resources"
    / "dashboard"
    / "tasks_dashboard.html"
)
for _p in (SCRIPTS_DIR, CHECK_TASKS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _state_envelope  # noqa: E402
import check_tasks  # type: ignore[import-not-found]  # noqa: E402
import resume_context  # noqa: E402
from tasks_server import TasksServer, find_available_port  # type: ignore[import-not-found]  # noqa: E402
from tests.test_rsdh_tasks_dashboard_ui import (  # noqa: E402
    _NODE_CDP_HELPER,
    _NODE_DOM_HARNESS_PREAMBLE,
    _resolve_chrome_binary,
    _run_node_script,
)


def _init_git_repo(root: Path) -> str:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "dev@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Dev"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"], cwd=root, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "[DEMO] Initial commit"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_task(
    epic_dir: Path, features_dir: Path, task_id: str, epic_slug: str, status: str
) -> None:
    content = (
        f'---\nid: "{task_id}"\nstatus: "{status}"\npriority: "high"\n'
        f'epic: "{epic_slug}"\norder: "a1"\n---\n\n# {task_id}\n'
    )
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / f"{task_id}.md").write_text(content, encoding="utf-8")
    if status == "done":
        done_dir = features_dir / "done"
        done_dir.mkdir(parents=True, exist_ok=True)
        (done_dir / f"{task_id}.md").write_text(content, encoding="utf-8")
        (features_dir / f"{task_id}.md").unlink(missing_ok=True)
    else:
        features_dir.mkdir(parents=True, exist_ok=True)
        (features_dir / f"{task_id}.md").write_text(content, encoding="utf-8")


def _eval_dashboard_js(test_body_js: str) -> dict[str, Any]:
    preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
        "__HTML_PATH__", json.dumps(str(DASHBOARD_HTML))
    )
    helper = (
        "\nfunction createDashboardContext() { "
        "return createFakeDomHarness(async () => ({ async json() { return {}; } })).sandbox; }\n"
    )
    return _run_node_script(preamble + helper + "\n" + test_body_js)


def test_ltsp_hp_06_chrome_cdp_live_stage_and_microstep_transitions(
    tmp_path: Path,
) -> None:
    """LTSP-HP-06: End-to-end headless Chrome CDP verifies live stage and micro-step transitions from Tasks to Quality Check to Cross-Model Review."""
    chrome_bin = _resolve_chrome_binary()
    assert chrome_bin and os.path.exists(chrome_bin), (
        f"Real Chrome binary required for LTSP-HP-06 CDP test, got: {chrome_bin}"
    )

    qa_scripts_dir = REPO_ROOT / "skills" / "quality_check" / "resources" / "scripts"
    ext_rev_dir = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
    for p in (qa_scripts_dir, ext_rev_dir):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import run_external_review  # type: ignore[import-not-found]
    import verify_polyglot_registry  # type: ignore[import-not-found]

    ws_root = tmp_path / "ws"
    repo = ws_root / "ai-agent-tools"
    sha = _init_git_repo(repo)
    slug = "demo_epic"
    epic_dir = repo / ".devtool" / "epic" / slug
    features_dir = repo / ".devtool" / "features"
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / f"{slug}.en.md").write_text(f"# {slug}\n", encoding="utf-8")
    (epic_dir / "principal_review.md").write_text(
        "# Principal Review\nRound 1\nVerdict: PASS\n", encoding="utf-8"
    )
    for idx in range(1, 9):
        _write_task(epic_dir, features_dir, f"task_0{idx}_step", slug, "done")
    _write_task(epic_dir, features_dir, "task_09_step", slug, "in-progress")

    resume_context.record_gate_approval(repo, slug, 1, "yes", by="architect")
    resume_context.record_gate_approval(repo, slug, 2, "yes", by="architect")
    _state_envelope.update_epic_heartbeat(
        repo,
        slug,
        stage="Stage 3 (Implementation)",
        sub_step="wave_2",
        sub_step_detail="Wave 2: 8/9 tasks done",
        last_event="Wave 2 implementing task_09_step",
        active_wave=2,
        slots={"1": {"task_id": "task_09_step", "status": "working"}},
        active_tasks=["task_09_step"],
    )

    server = TasksServer(
        host="127.0.0.1",
        port=find_available_port(19980),
        workspace_root=ws_root,
        pid_file=tmp_path / "tasks_server.pid",
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/"

    (tmp_path / "cdp_helper.mjs").write_text(_NODE_CDP_HELPER, encoding="utf-8")

    coord = verify_polyglot_registry._QualityRunCoordinator(
        run_id="qa-hp06-live",
        repo_root=repo,
        profile="epic",
        epic_slug=slug,
        heartbeat_interval=60.0,
        step_total=5,
        ttl_sec=120,
        planned_steps=[
            ("python-qa", "lint"),
            ("python-qa", "typecheck"),
            ("python-qa", "pytest_unit"),
            ("python-qa", "integration"),
            ("python-qa", "e2e"),
        ],
        head_sha=sha,
    )

    class _ControlHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def do_POST(self) -> None:
            if self.path.endswith("/quality"):
                _write_task(epic_dir, features_dir, "task_09_step", slug, "done")
                coord.start_step("python-qa", "lint")
                coord.complete_step(
                    "python-qa", "lint", status="passed", elapsed_sec=0.4
                )
                coord.start_step("python-qa", "typecheck")
                coord.complete_step(
                    "python-qa", "typecheck", status="passed", elapsed_sec=0.8
                )
                coord.start_step("python-qa", "pytest_unit")
            elif self.path.endswith("/review/reviewing"):
                coord.complete_step(
                    "python-qa", "pytest_unit", status="passed", elapsed_sec=1.2
                )
                coord.start_step("python-qa", "integration")
                coord.complete_step(
                    "python-qa", "integration", status="passed", elapsed_sec=0.9
                )
                coord.start_step("python-qa", "e2e")
                coord.complete_step(
                    "python-qa", "e2e", status="passed", elapsed_sec=1.1
                )
                coord.finalize("passed")
                _state_envelope.update_epic_heartbeat(
                    repo,
                    slug,
                    stage="Stage 3 Phase 4 (Review)",
                    sub_step="audit_epic",
                    last_event="audit_epic PASS; check_bdd_traceability PASS",
                )
                resume_context.record_gate_approval(repo, slug, 4, "yes", by="qa")
                run_external_review._emit_review_heartbeat(
                    repo,
                    slug,
                    kind="code",
                    phase="reviewing",
                    round_num=1,
                    max_rounds=3,
                    cli="codex",
                    model="gpt-6.1-sol",
                    detail="Codex reviewing Round 1",
                    sha=sha,
                )
            elif self.path.endswith("/review/triage"):
                run_external_review._emit_review_heartbeat(
                    repo,
                    slug,
                    kind="code",
                    phase="triage",
                    round_num=1,
                    max_rounds=3,
                    cli="codex",
                    model="gpt-6.1-sol",
                    verdict="CHANGES REQUIRED",
                    important=1,
                    action="AUTO_FIX_ELIGIBLE",
                    detail="Lập bảng triage: 1 Important",
                    sha=sha,
                )
            elif self.path.endswith("/review/fixing"):
                run_external_review._emit_review_heartbeat(
                    repo,
                    slug,
                    kind="code",
                    phase="fixing",
                    round_num=1,
                    max_rounds=3,
                    cli="codex",
                    model="gpt-6.1-sol",
                    verdict="CHANGES REQUIRED",
                    important=1,
                    action="AUTO_FIX_ELIGIBLE",
                    detail="Fix findings in Round 1",
                    sha=sha,
                )
            elif self.path.endswith("/review/verifying"):
                run_external_review._emit_review_heartbeat(
                    repo,
                    slug,
                    kind="code",
                    phase="verifying",
                    round_num=1,
                    max_rounds=3,
                    cli="codex",
                    model="gpt-6.1-sol",
                    verdict="CHANGES REQUIRED",
                    important=1,
                    action="AUTO_FIX_ELIGIBLE",
                    detail="Verifying Round 1 fixes",
                    sha=sha,
                )
            self.send_response(200)
            self.end_headers()

    ctrl_port = find_available_port(19995)
    ctrl_server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", ctrl_port), _ControlHandler
    )
    threading.Thread(target=ctrl_server.serve_forever, daemon=True).start()

    cdp_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(tmp_path / "cdp_helper.mjs"))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Page.navigate', {{ url: {json.dumps(url)} }});
  let ready = false;
  for (let i = 0; i < 50; i++) {{
    ready = await cdp.evaluate(`Boolean(document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools .epic-execution-item'))`);
    if (ready) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.ok(ready, 'Dashboard must render initial Tier 2 card from live TasksServer in Chrome CDP');
  await cdp.evaluate(`window.__ltspNoReloadMarker = 'alive'`);

  // Phase 1: Wave 2 Task Implementation (8/9 tasks)
  const sec2Wave = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  assert.match(sec2Wave, /8\s*\/\s*9\s*Hoàn thành/);
  assert.match(sec2Wave, /Wave 2/);

  // Phase 2: All Tasks Done (9/9 · 100%) running Quality Check (PyCore / Unit Test 3/5)
  const qaRes = await fetch({json.dumps(f"http://127.0.0.1:{ctrl_port}/quality")}, {{ method: 'POST' }});
  assert.equal(qaRes.status, 200);
  await cdp.evaluate(`pollDashboard()`);

  const sec2Qa = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  const kanbanQa = await cdp.evaluate(`document.getElementById('kanban-dashboard-wrapper-ai-agent-tools').innerText`);
  assert.match(sec2Qa, /9\s*\/\s*9\s*Hoàn thành/);
  assert.match(sec2Qa, /100%/);
  assert.match(sec2Qa, /PyCore \/ Unit Test/);
  assert.match(sec2Qa, /Static Lint/);
  assert.match(sec2Qa, /Typecheck/);
  assert.match(kanbanQa, /9\/9 Tasks \(100%\)/);

  // Phase 3a: Cross-Model Review Round 1 - Reviewing
  assert.equal((await fetch({json.dumps(f"http://127.0.0.1:{ctrl_port}/review/reviewing")}, {{ method: 'POST' }})).status, 200);
  await cdp.evaluate(`pollDashboard()`);
  const sec2Rev1 = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  assert.match(sec2Rev1, /Round 1\/3/);
  assert.match(sec2Rev1, /codex/);
  assert.match(sec2Rev1, /Reviewing/);

  // Phase 3b: Cross-Model Review Round 1 - Lập bảng triage
  assert.equal((await fetch({json.dumps(f"http://127.0.0.1:{ctrl_port}/review/triage")}, {{ method: 'POST' }})).status, 200);
  await cdp.evaluate(`pollDashboard()`);
  const sec2Triage = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  assert.match(sec2Triage, /Lập bảng triage/);
  assert.match(sec2Triage, /CHANGES REQUIRED/);

  // Phase 3c: Cross-Model Review Round 1 - Fix findings
  assert.equal((await fetch({json.dumps(f"http://127.0.0.1:{ctrl_port}/review/fixing")}, {{ method: 'POST' }})).status, 200);
  await cdp.evaluate(`pollDashboard()`);
  const sec2Fixing = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  assert.match(sec2Fixing, /Fix findings/);

  // Phase 3d: Cross-Model Review Round 1 - Verifying
  assert.equal((await fetch({json.dumps(f"http://127.0.0.1:{ctrl_port}/review/verifying")}, {{ method: 'POST' }})).status, 200);
  await cdp.evaluate(`pollDashboard()`);
  const sec2Rev = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  const kanbanRev = await cdp.evaluate(`document.getElementById('kanban-dashboard-wrapper-ai-agent-tools').innerText`);
  const marker = await cdp.evaluate(`window.__ltspNoReloadMarker`);

  assert.equal(marker, 'alive', 'Must update Section II in-place without reloading page');
  assert.match(sec2Rev, /9\s*\/\s*9\s*Hoàn thành/);
  assert.match(sec2Rev, /100%/);
  assert.match(sec2Rev, /Round 1\/3/);
  assert.match(sec2Rev, /Verifying/);
  assert.match(kanbanRev, /9\/9 Tasks \(100%\)/);
  assert.match(kanbanRev, /9[0-6]%/);
  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok', marker }}));
}} finally {{
  await cdp.close();
}}
"""
    try:
        res = _run_node_script(cdp_script, timeout=45)
        assert res["status"] == "ok"
    finally:
        ctrl_server.shutdown()
        ctrl_server.server_close()
        server.shutdown()
        server.server_close()


class TestLifecycleTelemetryAndStageProgress_Integration:
    """Integration test class proving Tier C provenance for LTSP Task 04 scenarios."""

    def test_ltsp_hp_06_integration(self, tmp_path: Path) -> None:
        """LTSP-HP-06: End-to-end headless Chrome CDP verifies live stage and micro-step transitions."""
        test_ltsp_hp_06_chrome_cdp_live_stage_and_microstep_transitions(tmp_path)

    def test_ltsp_ec_04_expandable_event_log_preserves_state_across_polls(self) -> None:
        """LTSP-EC-04: Expandable event log drawer preserves expanded state across live pollDashboard ticks."""
        res = _eval_dashboard_js(
            r"""
            let eventsCount = 8;
            function makeSnapshot(count) {
              const events = Array.from({ length: count }, (_, i) => ({
                ts: `2026-11-14T08:0${i}:00Z`,
                stage: 'Stage 3 Phase 4 (Review)',
                sub_step: 'triage',
                message: `Event log line #${i + 1}`,
              }));
              return {
                available_profiles: ['phungthuy8901'],
                repos: [{
                  name: 'ai-agent-tools',
                  path: '/tmp/ws/ai-agent-tools',
                  theme_color: '#38bdf8',
                  account_id: 'phungthuy8901',
                  active_epic: 'log_epic',
                  active_stage: 'Stage 3 Phase 4 (Review)',
                  prompt: 'Reviewing',
                  is_human_action_required: false,
                  worktrees: [],
                  task_progress: { total_tasks: 4, done_tasks: 4, in_progress_tasks: 0, todo_tasks: 0, percentage: 92.0, task_completion_pct: 100.0, tasks: [] },
                  epics_summary: {
                    total: 1,
                    completed: 0,
                    in_progress: 1,
                    unstarted: 0,
                    abandoned: 0,
                    epics: [{ slug: 'log_epic', title: 'Log Epic', status: 'in_progress', task_count: 4 }],
                  },
                  heartbeat: {
                    epic_slug: 'log_epic',
                    stage: 'Stage 3 Phase 4 (Review)',
                    sub_step: 'triage',
                    events,
                  },
                }],
              };
            }

            const { sandbox, doc } = createFakeDomHarness(async (url) => {
              if (String(url).includes('/api/tasks')) {
                return { async json() { return makeSnapshot(eventsCount); } };
              }
              return { async json() { return {}; } };
            });

            await sandbox.pollDashboard();
            const tier2El = doc.getElementById('tier2-execution-epics-wrapper-ai-agent-tools');
            assert.ok(tier2El, 'Tier 2 wrapper rendered');
            // Initially collapsed to 4 latest events (5..8)
            assert.doesNotMatch(tier2El.innerHTML, /Event log line #1\b/, 'Collapsed log must only show latest 4 events');
            assert.match(tier2El.innerHTML, /Event log line #8\b/);

            // Click toggle to expand all event logs, then force re-render
            sandbox.toggleEpicEventLogs('ai-agent-tools:log_epic');
            sandbox.renderRepoDetailView('ai-agent-tools', true);
            const tier2Expanded = doc.getElementById('tier2-execution-epics-wrapper-ai-agent-tools');
            assert.match(tier2Expanded.innerHTML, /Event log line #1\b/, 'Expanded log must display Event #1');
            assert.match(tier2Expanded.innerHTML, /Event log line #8\b/, 'Expanded log must display Event #8');

            // Next poll tick adds 9th event -> drawer must stay expanded and show all 9 events
            eventsCount = 9;
            await sandbox.pollDashboard();
            const tier2AfterPoll = doc.getElementById('tier2-execution-epics-wrapper-ai-agent-tools');
            assert.match(tier2AfterPoll.innerHTML, /Event log line #1\b/, 'Drawer must remain expanded on next poll tick');
            assert.match(tier2AfterPoll.innerHTML, /Event log line #9\b/, 'Drawer must render new 9th event');

            console.log(JSON.stringify({ status: 'ok', html: tier2AfterPoll.innerHTML }));
            """
        )
        assert res["status"] == "ok"
        assert "Event log line #1" in res["html"]
        assert "Event log line #9" in res["html"]

    def test_ltsp_st_04_commit_based_fix_and_verifying_inference(
        self, tmp_path: Path
    ) -> None:
        """LTSP-ST-04: Commit-based fix and verification detection infers fixing after commit and verifying only when verification executes."""
        repo = tmp_path / "repo_st04"
        sha1 = _init_git_repo(repo)
        epic_dir = repo / ".devtool" / "epic" / "rev_epic"
        features_dir = repo / ".devtool" / "features"
        _write_task(epic_dir, features_dir, "task_01", "rev_epic", "done")
        resume_context.record_gate_approval(repo, "rev_epic", 4, "Gate 4 PASS")

        # Round 1 recorded SHA: sha1 with CHANGES REQUIRED and 1 Important finding
        (epic_dir / "review_results.md").write_text(
            "## Round 1 — 2026-11-14T08:00:00Z\n"
            "- **Kind**: code\n"
            "- **Reviewer**: codex (gpt-6.1-sol)\n"
            f"- **SHA**: {sha1}\n"
            "- **Verdict**: CHANGES REQUIRED\n"
            "- **Counts**: 0 Critical · 1 Important · 0 Minor\n\n"
            "| ID | Severity | Location | Finding | Status |\n"
            "|---|---|---|---|---|\n"
            "| F1 | Important | src/app.py:10 | Missing edge case validation | Open |\n",
            encoding="utf-8",
        )

        # Create new commit sha2 and record 'fixed in <sha2>' in review_results.md
        (repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "app.py"], cwd=repo, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "[REV_EPIC] Fix validation edge case"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        sha2 = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        (epic_dir / "review_results.md").write_text(
            "## Round 1 — 2026-11-14T08:00:00Z\n"
            "- **Kind**: code\n"
            "- **Reviewer**: codex (gpt-6.1-sol)\n"
            f"- **SHA**: {sha1}\n"
            "- **Verdict**: CHANGES REQUIRED\n"
            "- **Counts**: 0 Critical · 1 Important · 0 Minor\n\n"
            "| ID | Severity | Location | Finding | Status |\n"
            "|---|---|---|---|---|\n"
            f"| F1 | Important | src/app.py:10 | Missing edge case validation | fixed in {sha2} |\n",
            encoding="utf-8",
        )

        prog = check_tasks.extract_task_progress(repo, "rev_epic")
        telem_fixing = check_tasks.build_epic_pipeline_telemetry(
            repo,
            "rev_epic",
            done_tasks=prog.done_tasks,
            total_tasks=prog.total_tasks,
            active_stage="Stage 3 Phase 4 (Review)",
            heartbeat=None,
            quality_active=None,
        )
        stage5_fixing = next(
            s for s in telem_fixing["stages"] if s["id"] == "cross_review"
        )
        sub_map_fixing = {s["id"]: s["status"] for s in stage5_fixing["sub_steps"]}
        assert sub_map_fixing["fixing"] == "running"
        assert sub_map_fixing["verifying"] == "pending"

        # Now start a verification execution on sha2 -> transitions to 'verifying'
        qa_state = _state_envelope.update_quality_run(
            repo,
            "qa-verify-sha2",
            epic_slug="rev_epic",
            profile="epic",
            status="running",
            provider="python-qa",
            capability="pycore",
            step_index=1,
            step_total=2,
        )
        qa_running = qa_state["runs"]["qa-verify-sha2"]
        telem_verifying = check_tasks.build_epic_pipeline_telemetry(
            repo,
            "rev_epic",
            done_tasks=prog.done_tasks,
            total_tasks=prog.total_tasks,
            active_stage="Stage 3 Phase 4 (Review)",
            heartbeat=None,
            quality_active=qa_running,
        )
        stage5_verifying = next(
            s for s in telem_verifying["stages"] if s["id"] == "cross_review"
        )
        sub_map_verifying = {
            s["id"]: s["status"] for s in stage5_verifying["sub_steps"]
        }
        assert sub_map_verifying["fixing"] == "done"
        assert sub_map_verifying["verifying"] == "running"

    def test_ltsp_ar_03_multi_epic_pipeline_telemetry_isolation(
        self, tmp_path: Path
    ) -> None:
        """LTSP-AR-03: Multi-epic workspace isolates pipeline_telemetry per epic across active and secondary in-progress epics."""
        repo = tmp_path / "repo_ar03"
        _init_git_repo(repo)
        features_dir = repo / ".devtool" / "features"

        # Primary active_epic: epic_alpha in Stage 3 Cross-Model Review (4/4 tasks · 100%)
        epic_alpha = repo / ".devtool" / "epic" / "epic_alpha"
        for i in range(1, 5):
            _write_task(
                epic_alpha, features_dir, f"task_0{i}_alpha", "epic_alpha", "done"
            )
        resume_context.record_gate_approval(repo, "epic_alpha", 4, "Gate 4 PASS")
        _state_envelope.update_epic_heartbeat(
            repo,
            "epic_alpha",
            stage="Stage 3 Phase 4 (Review)",
            sub_step="triage",
            sub_step_detail="Round 1/3: Lập bảng triage",
            review_state={
                "kind": "code",
                "round": 1,
                "max_rounds": 3,
                "cli": "codex",
                "model": "gpt-6.1-sol",
                "phase": "triage",
            },
            last_event="Alpha Cross-Model Review R1 triage",
        )

        # Secondary in_progress epic: epic_beta in Stage 2 Principal Review (0/3 tasks · 0%)
        epic_beta = repo / ".devtool" / "epic" / "epic_beta"
        epic_beta.mkdir(parents=True, exist_ok=True)
        (epic_beta / "epic_beta.en.md").write_text(
            "# Epic Beta HLD\n\n- **Status**: in_progress\n- **PIC**: phungthuy8901\n",
            encoding="utf-8",
        )
        for i in range(1, 4):
            (epic_beta / f"task_0{i}_beta.md").write_text(
                f'---\nid: "task_0{i}_beta"\nstatus: "todo"\nepic: "epic_beta"\n---\n# Beta {i}\n',
                encoding="utf-8",
            )
        resume_context.record_gate_approval(repo, "epic_beta", 1, "Gate 1 PASS")
        _state_envelope.update_epic_heartbeat(
            repo,
            "epic_beta",
            stage="Stage 2 (Architecture)",
            sub_step="reviewing",
            sub_step_detail="Principal Review R1: reviewing",
            review_state={
                "kind": "principal",
                "round": 1,
                "max_rounds": 3,
                "cli": "codex",
                "model": "gpt-6.1-sol",
                "phase": "reviewing",
            },
            last_event="Beta Principal Review R1 reviewing",
        )

        # Ensure epic_alpha is resolved as primary active_epic via assistant_state.md
        (repo / ".devtool" / "assistant_state.md").write_text(
            "# Active Epic: epic_alpha\n## Stage:\nStage 3 Phase 4 (Review)\n",
            encoding="utf-8",
        )

        meta = check_tasks.scan_repo(repo)
        assert meta.active_epic == "epic_alpha"
        assert meta.epics_summary is not None
        alpha_entry = next(
            e for e in meta.epics_summary.epics if e["slug"] == "epic_alpha"
        )
        beta_entry = next(
            e for e in meta.epics_summary.epics if e["slug"] == "epic_beta"
        )

        alpha_pt = alpha_entry["pipeline_telemetry"]
        beta_pt = beta_entry["pipeline_telemetry"]
        assert alpha_pt["task_completion_pct"] == 100.0
        assert alpha_pt["current_stage_index"] == 5
        assert beta_pt["task_completion_pct"] == 0.0
        assert beta_pt["current_stage_index"] == 2

        repo_dict = json.loads(json.dumps(meta, default=lambda o: o.__dict__))
        res = _eval_dashboard_js(
            rf"""
            const ctx = createDashboardContext();
            const repo = {json.dumps(repo_dict)};
            const execHtml = ctx.renderExecutionEpics(repo);
            const kanbanHtml = ctx.renderKanbanDashboard(repo, 'all');
            console.log(JSON.stringify({{ execHtml, kanbanHtml }}));
            """
        )
        assert "epic_alpha" in res["execHtml"]
        assert "epic_beta" in res["execHtml"]
        assert "4 / 4 Hoàn thành" in res["execHtml"]
        assert "0 / 0 Hoàn thành" in res["execHtml"] or "0%" in res["execHtml"]

    def test_ltsp_fr_03_corrupted_review_and_heartbeat_recovery(
        self, tmp_path: Path
    ) -> None:
        """LTSP-FR-03: Corrupted or truncated review_results.md / heartbeat.json files recover cleanly during pipeline harvesting."""
        repo = tmp_path / "repo_fr03"
        _init_git_repo(repo)
        epic_dir = repo / ".devtool" / "epic" / "corrupt_epic"
        features_dir = repo / ".devtool" / "features"
        _write_task(epic_dir, features_dir, "task_01", "corrupt_epic", "in-progress")

        state_dir = repo / ".devtool" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        # Write truncated JSON in .heartbeat.json
        (state_dir / "corrupt_epic.heartbeat.json").write_text(
            '{"epic_slug": "corrupt_epic", "events": [{"ts": "2026', encoding="utf-8"
        )
        # Write malformed markdown table rows in review_results.md
        (epic_dir / "review_results.md").write_text(
            "## Round 1 — 2026-11-14\n"
            "- **Kind**: code\n"
            "| broken | table\n"
            "|---|---|---|\n"
            "| F1 | Important\n",
            encoding="utf-8",
        )

        meta = check_tasks.scan_repo(repo)
        assert meta.active_epic == "corrupt_epic"
        assert meta.pipeline_telemetry is not None
        assert len(meta.pipeline_telemetry["stages"]) == 6
