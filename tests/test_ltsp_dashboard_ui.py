"""UI & Chrome CDP integration tests for tasks_dashboard.html 6-stage stepper,
sub-steps bar, dual 100% task vs weighted lifecycle progress, rolling event logs,
and Kanban TIẾN ĐỘ EPICS stage overview.

Covers BDD Scenarios:
- LTSP-HP-05: Tasks dashboard renders 6-stage stepper, sub-step micro-tracker, 100% task badge, rolling event logs, and Kanban TIẾN ĐỘ EPICS stage overview
- LTSP-EC-03: Dashboard degrades gracefully when legacy payloads omit pipeline_telemetry or events
- LTSP-ST-03: Quality Check sub-steps transition visually from Static Lint to Typecheck to PyCore/Unit Test to UI/E2E Test
- LTSP-AR-02: Section II tier2Sig detects sub-step, review_state, quality step, and event log changes without clobbering sibling Roadmap focus
- LTSP-FR-02: Failed or aborted quality step and Circuit Breaker review halt render explicit error badges in the stage stepper
"""

from __future__ import annotations

import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any

import pytest  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_HTML = (
    REPO_ROOT
    / "skills"
    / "check-tasks"
    / "resources"
    / "dashboard"
    / "tasks_dashboard.html"
)
CHECK_TASKS_SCRIPT_DIR = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
if str(CHECK_TASKS_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(CHECK_TASKS_SCRIPT_DIR))

from tasks_server import TasksHandler, TasksServer, find_available_port  # type: ignore[import-not-found]  # noqa: E402
from tests.test_rsdh_tasks_dashboard_ui import (  # noqa: E402
    _MutableTasksServer,
    _NODE_CDP_HELPER,
    _NODE_DOM_HARNESS_PREAMBLE,
    _resolve_chrome_binary,
    _run_node_script,
)


def _eval_dashboard_js(test_body_js: str) -> dict[str, Any]:
    preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
        "__HTML_PATH__", json.dumps(str(DASHBOARD_HTML))
    )
    helper = "\nfunction createDashboardContext() { return createFakeDomHarness(async () => ({ async json() { return {}; } })).sandbox; }\n"
    return _run_node_script(preamble + helper + "\n" + test_body_js)


# [LTSP-HP-05] Tasks dashboard renders 6-stage stepper, sub-step micro-tracker, 100% task badge, rolling event logs, and Kanban TIẾN ĐỘ EPICS stage overview
def test_ltsp_hp_05_stepper_substeps_logs_and_kanban_overview() -> None:
    """LTSP-HP-05: Tasks dashboard renders 6-stage stepper, sub-step micro-tracker, 100% task badge, rolling event logs, and Kanban TIẾN ĐỘ EPICS stage overview."""
    res = _eval_dashboard_js(
        r"""
        const ctx = createDashboardContext();
        const tasks = Array.from({ length: 9 }, (_, idx) => ({
          id: `task_0${idx + 1}`,
          title: `Task ${idx + 1}`,
          status: 'done',
          priority: 'high',
          epic: 'demo_epic',
        }));
        const events = Array.from({ length: 5 }, (_, idx) => ({
          ts: `2026-11-14T08:0${idx}:00Z`,
          stage: 'Stage 3 Phase 4 (Review)',
          sub_step: 'triage',
          message: `Cross-Model Review event #${idx + 1}`,
        }));
        const pipelineTelemetry = {
          epic_slug: 'demo_epic',
          task_completion_pct: 100.0,
          lifecycle_progress_pct: 92.0,
          current_stage_index: 5,
          active_sub_step_summary: 'Cross-Model Review R1/3 · Lập bảng triage (codex)',
          stages: [
            { id: 'spec', index: 1, label: '1. Spec', status: 'done', summary: 'Gate 1 PASS', sub_steps: [] },
            { id: 'hld_principal', index: 2, label: '2. HLD & Principal', status: 'done', summary: 'Gate 2 + Principal R2 PASS', sub_steps: [] },
            { id: 'tasks', index: 3, label: '3. Tasks', status: 'done', summary: '9/9 (100%)', sub_steps: [] },
            { id: 'gate4_quality', index: 4, label: '4. Gate 4 QA', status: 'done', summary: 'Audit + BDD + QA PASS', sub_steps: [] },
            {
              id: 'cross_review',
              index: 5,
              label: '5. Cross-Review',
              status: 'running',
              summary: 'Round 1/3 · codex (gpt-6.1-sol) · Lập bảng triage',
              sub_steps: [
                { id: 'reviewing', label: 'Reviewing', status: 'done', detail: 'codex (gpt-6.1-sol)' },
                { id: 'triage', label: 'Lập bảng triage', status: 'running', detail: '1 Important (AUTO_FIX_ELIGIBLE)' },
                { id: 'fixing', label: 'Fix findings', status: 'pending', detail: '' },
                { id: 'verifying', label: 'Verifying', status: 'pending', detail: '' },
              ],
            },
            { id: 'finish', index: 6, label: '6. Finish', status: 'pending', summary: 'Chờ Gate 5', sub_steps: [] },
          ],
          events,
        };
        const repo = {
          name: 'ai-agent-tools',
          path: '/tmp/ai-agent-tools',
          theme_color: '#38bdf8',
          account_id: 'phungthuy8901',
          active_epic: 'demo_epic',
          active_stage: 'Stage 3 Phase 4 (Review)',
          prompt: 'Đang lập bảng triage Cross-Model Review Round 1',
          is_human_action_required: false,
          worktrees: [{ path: '/tmp/ai-agent-tools/.worktrees/demo_epic', branch: 'epic/demo_epic', is_dirty: false, dirty_file_count: 0 }],
          task_progress: {
            total_tasks: 9,
            done_tasks: 9,
            in_progress_tasks: 0,
            todo_tasks: 0,
            percentage: 96.0,
            task_completion_pct: 100.0,
            tasks,
          },
          epics_summary: {
            total: 1,
            completed: 0,
            in_progress: 1,
            unstarted: 0,
            abandoned: 0,
            epics: [{
              slug: 'demo_epic',
              title: 'Demo Epic',
              status: 'in_progress',
              task_count: 9,
              pic: 'phungthuy8901',
              pipeline_telemetry: pipelineTelemetry,
            }],
          },
          heartbeat: {
            epic_slug: 'demo_epic',
            stage: 'Stage 3 Phase 4 (Review)',
            sub_step: 'triage',
            sub_step_detail: 'Lập bảng triage: CHANGES REQUIRED (1I)',
            review_state: {
              kind: 'code',
              round: 1,
              max_rounds: 3,
              cli: 'codex',
              model: 'gpt-6.1-sol',
              phase: 'triage',
              verdict: 'CHANGES REQUIRED',
              action: 'AUTO_FIX_ELIGIBLE',
            },
            events,
          },
          pipeline_telemetry: pipelineTelemetry,
        };

        const execHtml = ctx.renderExecutionEpics(repo);
        const kanbanHtml = ctx.renderKanbanDashboard(repo, 'all');

        console.log(JSON.stringify({
          execHtml,
          kanbanHtml,
        }));
        """
    )
    exec_html = res["execHtml"]
    kanban_html = res["kanbanHtml"]

    assert "9 / 9 Hoàn thành" in exec_html
    assert "100%" in exec_html
    assert 'data-telemetry="pipeline-stepper"' in exec_html
    for stage_lbl in (
        "1. Spec",
        "2. HLD &amp; Principal",
        "3. Tasks",
        "4. Gate 4 QA",
        "5. Cross-Review",
        "6. Finish",
    ):
        assert stage_lbl in exec_html
    assert 'data-telemetry="sub-steps"' in exec_html
    for micro_lbl in ("Reviewing", "Lập bảng triage", "Fix findings", "Verifying"):
        assert micro_lbl in exec_html
    assert "Round 1/3" in exec_html
    assert "codex" in exec_html
    assert 'data-telemetry="event-logs"' in exec_html
    assert "Cross-Model Review event #5" in exec_html

    assert "92%" in kanban_html
    assert "9/9 Tasks (100%)" in kanban_html
    assert 'data-telemetry="kanban-epic-stage"' in kanban_html
    assert "Lập bảng triage" in kanban_html or "Cross-Model Review" in kanban_html


class TestLtspDashboardUi_Integration:
    """Integration harness tests for LTSP Task 03 dashboard UI scenarios."""

    def test_ltsp_hp_05_integration(self) -> None:
        test_ltsp_hp_05_stepper_substeps_logs_and_kanban_overview()

    def test_ltsp_ec_03_legacy_payload_graceful_fallback(self) -> None:
        """LTSP-EC-03: Dashboard degrades gracefully when legacy payloads omit pipeline_telemetry or events."""
        res = _eval_dashboard_js(
            r"""
            const ctx = createDashboardContext();
            const tasks = Array.from({ length: 4 }, (_, idx) => ({
              id: `task_0${idx + 1}`,
              title: `Task ${idx + 1}`,
              status: 'done',
              priority: 'medium',
              epic: 'legacy_epic',
            }));
            const repo = {
              name: 'legacy-repo',
              path: '/tmp/legacy-repo',
              active_epic: 'legacy_epic',
              active_stage: 'Stage 3 Phase 4 (Review)',
              task_progress: {
                total_tasks: 4,
                done_tasks: 4,
                in_progress_tasks: 0,
                todo_tasks: 0,
                percentage: 96.0,
                tasks,
              },
              epics_summary: {
                total: 1,
                in_progress: 1,
                epics: [{ slug: 'legacy_epic', title: 'Legacy Epic', status: 'in_progress', task_count: 4 }],
              },
            };
            const progState = ctx.computeEpicProgressState(repo, 'legacy_epic', 4, 4, repo.epics_summary.epics[0]);
            const tddRepo = { ...repo, active_stage: 'Stage 3 Phase 2 (TDD)' };
            const tddState = ctx.computeEpicProgressState(tddRepo, 'legacy_epic', 4, 4, {});
            const signoffRepo = { ...repo, active_stage: 'Stage 3 Phase 4.1 (Sign-off)' };
            const signoffState = ctx.computeEpicProgressState(signoffRepo, 'legacy_epic', 4, 4, {});
            const execHtml = ctx.renderExecutionEpics(repo);
            const kanbanHtml = ctx.renderKanbanDashboard(repo, 'all');
            console.log(JSON.stringify({ progState, tddState, signoffState, execHtml, kanbanHtml }));
            """
        )
        prog_state = res["progState"]
        assert prog_state["taskPct"] == 100
        assert prog_state["pct"] == 92
        assert res["tddState"]["pct"] == 80
        assert res["tddState"]["taskPct"] == 100
        assert res["signoffState"]["pct"] == 98
        assert "4 / 4 Hoàn thành" in res["execHtml"]
        assert "100%" in res["execHtml"]
        assert "92% Review" in res["execHtml"]

    def test_ltsp_st_03_quality_check_substeps_visual_transition(self) -> None:
        """LTSP-ST-03: Quality Check sub-steps transition visually from Static Lint to Typecheck to PyCore/Unit Test to UI/E2E Test."""
        res = _eval_dashboard_js(
            r"""
            const ctx = createDashboardContext();
            const repo = {
              name: 'qa-repo',
              path: '/tmp/qa-repo',
              active_epic: 'qa_epic',
              active_stage: 'Stage 3 Phase 4 (Review)',
              task_progress: { total_tasks: 4, done_tasks: 4, in_progress_tasks: 0, todo_tasks: 0, percentage: 85.0, task_completion_pct: 100.0, tasks: [] },
              epics_summary: { total: 1, in_progress: 1, epics: [{ slug: 'qa_epic', status: 'in_progress', task_count: 4 }] },
              quality_active: {
                runs: {
                  'qa-run-1': {
                    run_id: 'qa-run-1',
                    epic_slug: 'qa_epic',
                    provider: 'python-qa',
                    capability: 'pycore',
                    capability_label: 'PyCore / Unit Test',
                    step_index: 3,
                    step_total: 4,
                    status: 'running',
                    elapsed_sec: 4.2,
                    steps: [
                      { index: 1, provider: 'python-qa', capability: 'lint', label: 'Static Lint', status: 'passed', elapsed_sec: 0.5 },
                      { index: 2, provider: 'python-qa', capability: 'typecheck', label: 'Typecheck', status: 'passed', elapsed_sec: 1.1 },
                      { index: 3, provider: 'python-qa', capability: 'pycore', label: 'PyCore / Unit Test', status: 'running', elapsed_sec: 4.2 },
                      { index: 4, provider: 'python-qa', capability: 'e2e', label: 'UI / E2E Test', status: 'pending', elapsed_sec: null },
                    ],
                  },
                },
              },
            };
            const execHtml = ctx.renderExecutionEpics(repo);
            console.log(JSON.stringify({ execHtml }));
            """
        )
        html = res["execHtml"]
        assert 'data-telemetry="quality"' in html
        assert "Static Lint" in html
        assert "Typecheck" in html
        assert "PyCore / Unit Test" in html
        assert "UI / E2E Test" in html

    def test_ltsp_ar_02_tier2_sig_updates_without_clobbering_roadmap_focus(
        self,
        tmp_path: Path,
    ) -> None:
        """LTSP-AR-02: Section II tier2Sig detects sub-step, review_state, quality step, and event log changes without clobbering sibling Roadmap focus."""
        res = _eval_dashboard_js(
            r"""
            const ctx = createDashboardContext();
            const baseRepo = {
              name: 'ar02-repo',
              path: '/tmp/ar02-repo',
              active_epic: 'ar_epic',
              active_stage: 'Stage 3 Phase 4 (Review)',
              task_progress: { total_tasks: 2, done_tasks: 2, in_progress_tasks: 0, todo_tasks: 0, percentage: 92.0, task_completion_pct: 100.0, tasks: [] },
              epics_summary: {
                total: 1,
                in_progress: 1,
                epics: [{ slug: 'ar_epic', title: 'AR Epic', status: 'in_progress', task_count: 2, pic: 'duedd' }],
              },
              heartbeat: {
                epic_slug: 'ar_epic',
                stage: 'Stage 3 Phase 4 (Review)',
                sub_step: 'triage',
                review_state: { kind: 'code', round: 1, max_rounds: 3, cli: 'codex', model: 'gpt-6.1-sol', phase: 'triage' },
                events: [{ ts: '2026-11-14T08:00:00Z', stage: 'Review', sub_step: 'triage', message: 'triage done' }],
              },
            };
            const nextRepo = JSON.parse(JSON.stringify(baseRepo));
            nextRepo.heartbeat.sub_step = 'fixing';
            nextRepo.heartbeat.review_state.phase = 'fixing';
            nextRepo.heartbeat.events.push({ ts: '2026-11-14T08:01:00Z', stage: 'Review', sub_step: 'fixing', message: 'fixing started' });

            const sig1 = ctx.buildTier2Sig(baseRepo);
            const sig2 = ctx.buildTier2Sig(nextRepo);
            const kSig1 = ctx.buildKanbanSig(baseRepo, 'all');
            const kSig2 = ctx.buildKanbanSig(nextRepo, 'all');
            const rSig1 = ctx.buildRoadmapSig(baseRepo);
            const rSig2 = ctx.buildRoadmapSig(nextRepo);

            console.log(JSON.stringify({
              tier2Changed: sig1 !== sig2,
              kanbanChanged: kSig1 !== kSig2,
              roadmapUnchanged: rSig1 === rSig2,
            }));
            """
        )
        assert res["tier2Changed"] is True
        assert res["kanbanChanged"] is True
        assert res["roadmapUnchanged"] is True

        # Live Chrome CDP assertion verifying <select> focus in Section III survives pipeline_telemetry sub-step updates
        chrome_bin = _resolve_chrome_binary()

        def _make_payload(
            *,
            qa_cap: str,
            qa_label: str,
            step_index: int,
            pct: float,
            event_msg: str,
        ) -> dict[str, Any]:
            pt = {
                "epic_slug": "ar_epic",
                "task_completion_pct": 100.0,
                "lifecycle_progress_pct": pct,
                "current_stage_index": 4,
                "active_sub_step_summary": f"Gate 4 QA · {qa_label}",
                "stages": [
                    {
                        "id": "spec",
                        "index": 1,
                        "label": "1. Spec",
                        "status": "done",
                        "summary": "Gate 1 PASS",
                        "sub_steps": [],
                    },
                    {
                        "id": "hld_principal",
                        "index": 2,
                        "label": "2. HLD & Principal",
                        "status": "done",
                        "summary": "HLD PASS",
                        "sub_steps": [],
                    },
                    {
                        "id": "tasks",
                        "index": 3,
                        "label": "3. Tasks",
                        "status": "done",
                        "summary": "2/2 (100%)",
                        "sub_steps": [],
                    },
                    {
                        "id": "gate4_quality",
                        "index": 4,
                        "label": "4. Gate 4 QA",
                        "status": "running",
                        "summary": qa_label,
                        "sub_steps": [
                            {
                                "id": "qa_lint",
                                "label": "Static Lint",
                                "status": "done" if step_index > 1 else "running",
                                "detail": "0.5s",
                            },
                            {
                                "id": "qa_unit",
                                "label": "PyCore / Unit Test",
                                "status": "running" if step_index == 2 else "done",
                                "detail": "1.2s",
                            },
                            {
                                "id": "qa_int",
                                "label": "Integration Test",
                                "status": "running" if step_index == 3 else "pending",
                                "detail": "",
                            },
                        ],
                    },
                    {
                        "id": "cross_review",
                        "index": 5,
                        "label": "5. Cross-Review",
                        "status": "pending",
                        "summary": "Pending",
                        "sub_steps": [],
                    },
                    {
                        "id": "finish",
                        "index": 6,
                        "label": "6. Finish",
                        "status": "pending",
                        "summary": "Pending",
                        "sub_steps": [],
                    },
                ],
                "events": [
                    {
                        "ts": "2026-11-14T08:00:00Z",
                        "stage": "Gate 4 QA",
                        "sub_step": qa_cap,
                        "message": event_msg,
                    },
                ],
            }
            return {
                "timestamp": 1730000000 + step_index,
                "accounts": ["brother", "tess"],
                "repos": [
                    {
                        "name": "ai-agent-tools",
                        "path": "/tmp/ar02-repo",
                        "theme_color": "#38bdf8",
                        "account_id": "brother",
                        "active_epic": "ar_epic",
                        "active_stage": "Stage 3 Phase 4 (Gate 4 QA)",
                        "prompt": f"Running {qa_label}",
                        "is_human_action_required": False,
                        "worktrees": [
                            {
                                "path": "/tmp/ar02-repo/.worktrees/ar_epic",
                                "branch": "epic/ar_epic",
                                "is_dirty": False,
                                "dirty_file_count": 0,
                            }
                        ],
                        "task_progress": {
                            "total_tasks": 2,
                            "done_tasks": 2,
                            "in_progress_tasks": 0,
                            "todo_tasks": 0,
                            "percentage": 85.0,
                            "task_completion_pct": 100.0,
                            "tasks": [
                                {
                                    "id": "t1",
                                    "title": "Task 1",
                                    "status": "done",
                                    "priority": "high",
                                    "epic": "ar_epic",
                                },
                                {
                                    "id": "t2",
                                    "title": "Task 2",
                                    "status": "done",
                                    "priority": "high",
                                    "epic": "ar_epic",
                                },
                                {
                                    "id": "t3",
                                    "title": "Backlog Task",
                                    "status": "todo",
                                    "priority": "low",
                                    "epic": "sibling-backlog",
                                },
                            ],
                        },
                        "epics_summary": {
                            "total": 2,
                            "completed": 0,
                            "in_progress": 1,
                            "unstarted": 1,
                            "abandoned": 0,
                            "epics": [
                                {
                                    "slug": "ar_epic",
                                    "title": "AR Epic",
                                    "status": "in_progress",
                                    "task_count": 2,
                                    "pic": "brother",
                                    "pipeline_telemetry": pt,
                                },
                                {
                                    "slug": "sibling-backlog",
                                    "title": "Sibling Backlog",
                                    "status": "unstarted",
                                    "task_count": 1,
                                    "pic": "brother",
                                },
                            ],
                        },
                        "heartbeat": {
                            "epic_slug": "ar_epic",
                            "stage": "Stage 3 Phase 4 (Gate 4 QA)",
                            "sub_step": qa_cap,
                            "events": pt["events"],
                        },
                        "pipeline_telemetry": pt,
                    }
                ],
            }

        payload_1 = _make_payload(
            qa_cap="pytest_unit",
            qa_label="PyCore / Unit Test",
            step_index=2,
            pct=83.0,
            event_msg="qa running PyCore / Unit Test",
        )
        payload_2 = _make_payload(
            qa_cap="integration",
            qa_label="Integration Test",
            step_index=3,
            pct=85.0,
            event_msg="qa running Integration Test",
        )

        server = _MutableTasksServer(payload_1)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{server.server_port}/"
        (tmp_path / "cdp_ar02.mjs").write_text(_NODE_CDP_HELPER, encoding="utf-8")

        class _CtrlHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                return

            def do_POST(self) -> None:
                server.payload = payload_2
                self.send_response(200)
                self.end_headers()

        ctrl_port = find_available_port(19960)
        ctrl_server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", ctrl_port), _CtrlHandler
        )
        threading.Thread(target=ctrl_server.serve_forever, daemon=True).start()

        cdp_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(tmp_path / "cdp_ar02.mjs"))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Page.navigate', {{ url: {json.dumps(url)} }});
  let ready = false;
  for (let i = 0; i < 40; i++) {{
    ready = await cdp.evaluate(`Boolean(document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap[data-row-key="ai-agent-tools:sibling-backlog"]'))`);
    if (ready) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.ok(ready, 'Roadmap sibling select must render in Chrome CDP');

  const sec2Before = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  assert.match(sec2Before, /PyCore \/ Unit Test/);

  await cdp.evaluate(`(() => {{
    const sel = document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap[data-row-key="ai-agent-tools:sibling-backlog"]');
    window.__ltspSibSel = sel;
    sel.focus();
  }})()`);

  const mutRes = await fetch({json.dumps(f"http://127.0.0.1:{ctrl_port}/mutate")}, {{ method: 'POST' }});
  assert.equal(mutRes.status, 200);
  await cdp.evaluate(`pollDashboard()`);

  const during = await cdp.evaluate(`(() => {{
    const sec2 = document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText;
    const sel = document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap[data-row-key="ai-agent-tools:sibling-backlog"]');
    return {{
      sec2,
      sameNode: sel === window.__ltspSibSel,
      stillFocused: document.activeElement === window.__ltspSibSel,
    }};
  }})()`);
  assert.equal(during.sameNode, true, 'Focused Roadmap <select> DOM node must be preserved');
  assert.equal(during.stillFocused, true, 'Focused Roadmap <select> must keep activeElement focus');
  assert.match(during.sec2, /Integration Test/, 'Section II must update sub-step in place');
  assert.match(during.sec2, /qa running Integration Test/, 'Section II must render updated event log');
  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok' }}));
}} finally {{
  await cdp.close();
}}
"""
        try:
            cdp_res = _run_node_script(cdp_script, timeout=45)
            assert cdp_res["status"] == "ok"
        finally:
            ctrl_server.shutdown()
            ctrl_server.server_close()
            server.shutdown()
            server.server_close()

    def test_ltsp_fr_02_failed_quality_and_circuit_breaker_halt_badges(self) -> None:
        """LTSP-FR-02: Failed or aborted quality step and Circuit Breaker review halt render explicit error badges in the stage stepper."""
        res = _eval_dashboard_js(
            r"""
            const ctx = createDashboardContext();
            const qaFailRepo = {
              name: 'fr02-repo',
              path: '/tmp/fr02-repo',
              active_epic: 'fail_epic',
              active_stage: 'Stage 3 Phase 4 (Review)',
              task_progress: { total_tasks: 3, done_tasks: 3, in_progress_tasks: 0, todo_tasks: 0, percentage: 85.0, task_completion_pct: 100.0, tasks: [] },
              epics_summary: { total: 1, in_progress: 1, epics: [{ slug: 'fail_epic', status: 'in_progress', task_count: 3 }] },
              quality_active: {
                runs: {
                  'qa-fail': {
                    run_id: 'qa-fail',
                    epic_slug: 'fail_epic',
                    provider: 'python-qa',
                    capability: 'integration',
                    capability_label: 'Integration Test',
                    step_index: 2,
                    step_total: 3,
                    status: 'failed',
                    steps: [
                      { index: 1, provider: 'python-qa', capability: 'lint', label: 'Static Lint', status: 'passed' },
                      { index: 2, provider: 'python-qa', capability: 'integration', label: 'Integration Test', status: 'failed' },
                      { index: 3, provider: 'python-qa', capability: 'e2e', label: 'UI / E2E Test', status: 'pending' },
                    ],
                  },
                },
              },
            };
            const cbRepo = {
              name: 'cb-repo',
              path: '/tmp/cb-repo',
              active_epic: 'cb_epic',
              active_stage: 'Stage 3 Phase 4 (Review)',
              task_progress: { total_tasks: 3, done_tasks: 3, in_progress_tasks: 0, todo_tasks: 0, percentage: 92.0, task_completion_pct: 100.0, tasks: [] },
              epics_summary: { total: 1, in_progress: 1, epics: [{ slug: 'cb_epic', status: 'in_progress', task_count: 3 }] },
              heartbeat: {
                epic_slug: 'cb_epic',
                stage: 'Stage 3 Phase 4 (Review)',
                sub_step: 'triage',
                review_state: {
                  kind: 'code',
                  round: 3,
                  max_rounds: 3,
                  cli: 'codex',
                  model: 'gpt-6.1-sol',
                  phase: 'triage',
                  verdict: 'CHANGES REQUIRED',
                  action: 'CIRCUIT_BREAKER_HALT',
                },
              },
            };

            console.log(JSON.stringify({
              qaFailHtml: ctx.renderExecutionEpics(qaFailRepo),
              cbHtml: ctx.renderExecutionEpics(cbRepo),
            }));
            """
        )
        assert "Integration Test" in res["qaFailHtml"]
        assert "failed" in res["qaFailHtml"].lower()
        assert "CIRCUIT_BREAKER_HALT" in res["cbHtml"]
