"""End-to-end headless Chrome CDP & verify registry tests for CEHM-FR-02.

BDD Traceability:
- CEHM-FR-02: End-to-End Chrome CDP & Regression Alignment
"""

from __future__ import annotations

import ast
import contextlib
import http.server
import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_tasks  # type: ignore[import-not-found]  # noqa: E402
from tasks_server import (  # type: ignore[import-not-found]  # noqa: E402
    TasksHandler,
    TasksServer,
    find_available_port,
)
from tests.test_rsdh_tasks_dashboard_ui import (  # noqa: E402
    _NODE_CDP_HELPER,
    _resolve_chrome_binary,
    _run_node_script,
)

CEHM_VERIFY_SUITES = (
    "tests/test_cehm_telemetry_stream.py",
    "tests/test_cehm_history_aggregator.py",
    "tests/test_cehm_dashboard_modal_ui.py",
    "tests/test_cehm_e2e_cdp.py",
)


class _ControllableTasksHandler(TasksHandler):
    """TasksHandler subclass supporting one-shot HTTP 500 error injection for E2E."""

    def _handle_epic_history(self, query: dict[str, list[str]]) -> None:
        state = getattr(self.server, "cehm_test_state", None)
        if isinstance(state, dict) and state.get("fail_next_history_once"):
            state["fail_next_history_once"] = False
            self._send_json(
                500,
                {
                    "success": False,
                    "error": "Simulated HTTP 500 error from /api/epic/history",
                },
            )
            return
        super()._handle_epic_history(query)


def _make_control_handler(
    server_state: dict[str, bool],
) -> type[http.server.BaseHTTPRequestHandler]:
    """Create HTTP control handler toggling failure injection on the test TasksServer."""

    class _ControlHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path == "/arm-500":
                server_state["fail_next_history_once"] = True
                body = b'{"armed": true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    return _ControlHandler


def _git_run(repo_dir: Path, *args: str) -> None:
    """Execute a git command inside `repo_dir` failing immediately on error."""
    subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_git_repo(repo_dir: Path) -> None:
    """Create a real git repository with an initial commit."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    _git_run(repo_dir, "init")
    _git_run(repo_dir, "config", "user.email", "cehm-e2e@example.com")
    _git_run(repo_dir, "config", "user.name", "CEHM E2E")
    (repo_dir / "README.md").write_text("# CEHM E2E Fixture\n", encoding="utf-8")
    _git_run(repo_dir, "add", "README.md")
    _git_run(repo_dir, "commit", "-m", "[CEHM] Init fixture repo")


def _write_text(path: Path, content: str) -> None:
    """Write UTF-8 text ensuring parent directories exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_task_evidence_payload(idx: int) -> dict[str, Any]:
    """Return a real `run_task_checks.py`-shaped evidence JSON payload for task `idx`."""
    stem = f"task_{idx:02d}_fixture_{idx:02d}"
    return {
        "schema": 1,
        "task": stem,
        "runs": {
            "red": {
                "head": "abc1234",
                "started": f"2026-11-14T10:{idx:02d}:00Z",
                "finished": f"2026-11-14T10:{idx:02d}:05Z",
                "rows": [
                    {
                        "id": "V1",
                        "phase": "RED",
                        "command": f"python3 -m pytest -q tests/test_{stem}.py",
                        "expect": 'exit 1; contains "failed"',
                        "needs": [],
                        "exit": 1,
                        "outcome": "PASS",
                        "reason": None,
                        "output_tail": [
                            f"V1 RED check output_tail for task {idx:02d}",
                            "1 failed in 0.12s",
                        ],
                    }
                ],
                "passed": True,
            },
            "verify": {
                "head": "abc1234",
                "started": f"2026-11-14T10:{idx:02d}:10Z",
                "finished": f"2026-11-14T10:{idx:02d}:20Z",
                "rows": [
                    {
                        "id": "V2",
                        "phase": "GREEN",
                        "command": f"python3 -m pytest -q tests/test_{stem}.py",
                        "expect": 'exit 0; contains "passed"',
                        "needs": [],
                        "exit": 0,
                        "outcome": "PASS",
                        "reason": None,
                        "output_tail": [
                            f"V2 GREEN verification output_tail for task {idx:02d}",
                            "5 passed in 0.25s",
                        ],
                    }
                ],
                "passed": True,
            },
        },
    }


def _seed_done_epic(repo_dir: Path) -> None:
    """Seed completed `done_epic` with 11 tasks, >20 archived events, and 2-round reviews."""
    devtool = repo_dir / ".devtool"
    done_dir = devtool / "epic" / "done_epic"

    _write_text(
        devtool / "PROJECT_LEDGER.md",
        "# Project Ledger\n\n"
        "- **[2026-11-14] `done_epic`**: Completed (11 tasks, 2-round reviews).\n",
    )
    _write_text(
        done_dir / "done_epic.en.md",
        "# Epic: done_epic\n\n"
        "- **Status**: Done\n"
        "- **PIC**: phungthuy8901\n"
        "- **Branch**: `epic/done_epic`\n\n"
        "## Overview\n"
        "Completed epic fixture for headless Chrome CDP history modal verification.\n",
    )

    for idx in range(1, 12):
        stem = f"task_{idx:02d}_fixture_{idx:02d}"
        _write_text(
            done_dir / f"{stem}.md",
            "---\n"
            "epic: done_epic\n"
            "status: done\n"
            "priority: P1\n"
            f"title: Done Task {idx:02d}\n"
            "---\n\n"
            f"# Done Task {idx:02d}\n\n"
            f"Completed fixture task {idx:02d}.\n",
        )
        _write_text(
            done_dir / "evidence" / f"{stem}.json",
            json.dumps(_build_task_evidence_payload(idx), indent=2) + "\n",
        )

    gate_rows = [
        json.dumps(
            {
                "gate": gate_num,
                "epic": "done_epic",
                "timestamp": f"2026-11-14T0{gate_num}:00:00Z",
                "approver": "Human Architect",
                "summary": f"Gate {gate_num} approved for done_epic",
            }
        )
        for gate_num in range(1, 6)
    ]
    _write_text(
        devtool / "state" / "gate_ledger.jsonl",
        "\n".join(gate_rows) + "\n",
    )

    archived_events = [
        json.dumps(
            {
                "ts": f"2026-11-14T10:{idx:02d}:00Z",
                "stage": "Stage 3 (in-progress)",
                "sub_step": f"step_{idx:02d}",
                "sub_step_detail": f"Step detail {idx:02d}",
                "message": f"Archived step event {idx:02d} executed",
            }
        )
        for idx in range(1, 26)
    ]
    _write_text(
        devtool / "archive" / "events_done-epic_20261114_1200.jsonl",
        "\n".join(archived_events) + "\n",
    )
    _write_text(
        devtool / "archive" / "activity_done-epic_20261114_1200.log",
        "# Archived Activity Log\n"
        "- [2026-11-14 11:50] Archived activity summary for done_epic\n",
    )

    _write_text(
        done_dir / "principal_review.md",
        "# Principal Review: done_epic\n\n"
        "## Round 1\n\n"
        "- **Date**: 2026-11-14T02:00:00Z\n"
        "- **SHA**: 1111111\n"
        "- **CLI**: claude\n"
        "- **Model**: Opus 5.5\n"
        "- **Status**: completed\n"
        "- **Verdict**: CHANGES REQUIRED\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        "| 1 | Important | done_epic.en.md:10 | Round 1 Principal important finding | Fixed |\n\n"
        "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n\n"
        "## Round 2\n\n"
        "- **Date**: 2026-11-14T02:30:00Z\n"
        "- **SHA**: 2222222\n"
        "- **CLI**: claude\n"
        "- **Model**: Opus 5.5\n"
        "- **Status**: completed\n"
        "- **Verdict**: PASS\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        "| 1 | Minor | done_epic.en.md:12 | Round 2 Principal minor check | Noted |\n\n"
        "Raw output:\n\n```text\nVerdict: PASS\n```\n",
    )
    _write_text(
        done_dir / "review_results.md",
        "# Cross-Model Review: done_epic\n\n"
        "## Round 1\n\n"
        "- **Date**: 2026-11-14T04:00:00Z\n"
        "- **SHA**: 3333333\n"
        "- **CLI**: codex\n"
        "- **Model**: gpt-6.1-sol\n"
        "- **Status**: completed\n"
        "- **Verdict**: CHANGES REQUIRED\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        "| 1 | Important | server.py:42 | Round 1 Cross-Model important finding | Fixed |\n\n"
        "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n\n"
        "## Round 2\n\n"
        "- **Date**: 2026-11-14T04:30:00Z\n"
        "- **SHA**: 4444444\n"
        "- **CLI**: codex\n"
        "- **Model**: gpt-6.1-sol\n"
        "- **Status**: completed\n"
        "- **Verdict**: PASS\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        "| 1 | Minor | server.py:88 | Round 2 Cross-Model minor polish | Fixed |\n\n"
        "Raw output:\n\n```text\nVerdict: PASS\n```\n",
    )


def _seed_in_prog_and_backlog_epics(repo_dir: Path) -> None:
    """Seed active `in_prog_epic` in a git worktree and unstarted `backlog_epic` HLD."""
    _write_text(
        repo_dir / ".devtool" / "epic" / "in_prog_epic" / "in_prog_epic.en.md",
        "# Epic: in_prog_epic\n\n"
        "- **Status**: In Progress\n"
        "- **PIC**: danhdue\n"
        "- **Branch**: `epic/in_prog_epic`\n\n"
        "## Overview\n"
        "Active live execution epic rendered inside Section II.\n",
    )
    _write_text(
        repo_dir
        / ".devtool"
        / "epic"
        / "backlog_epic"
        / "2026-11-15-backlog-epic-design.en.md",
        "# Design Spec: backlog_epic\n\n"
        "- **Status**: Draft\n"
        "- **PIC**: brother\n\n"
        "## Problem\n"
        "Unstarted backlog epic with HLD design draft only and no tasks or logs.\n",
    )
    _git_run(repo_dir, "add", ".devtool")
    _git_run(repo_dir, "commit", "-m", "[CEHM] Seed fixture epics")

    wt_dir = repo_dir / ".worktrees" / "in_prog_epic"
    wt_dir.parent.mkdir(parents=True, exist_ok=True)
    _git_run(
        repo_dir,
        "worktree",
        "add",
        "-b",
        "epic/in_prog_epic",
        str(wt_dir),
    )
    _write_text(
        wt_dir / ".devtool" / "features" / "task_01_live_execution_card.md",
        "---\n"
        "epic: in_prog_epic\n"
        "status: in-progress\n"
        "priority: P0\n"
        "title: Live Execution Task\n"
        "---\n\n"
        "# Live Execution Task\n",
    )
    _write_text(
        wt_dir / ".devtool" / "state" / "in_prog_epic.heartbeat.json",
        json.dumps(
            {
                "schema_version": 1,
                "generation": 1,
                "epic": "in_prog_epic",
                "stage": "Stage 3 (in-progress: task_01_live_execution_card)",
                "sub_step": "tdd_green",
                "sub_step_detail": "Running live Section II card verification",
                "updated_at": "2026-11-15T00:00:00Z",
                "is_stale": False,
            },
            indent=2,
        )
        + "\n",
    )


def _extract_verify_suites(
    verify_sh_path: Path,
) -> list[tuple[str, str, str, int, bool]]:
    """Parse the Python `SUITES` list literal embedded inside `scripts/verify.sh`."""
    content = verify_sh_path.read_text(encoding="utf-8")
    marker = "SUITES = ["
    start = content.find(marker)
    assert start != -1, "Missing SUITES definition in scripts/verify.sh"
    end = content.find("\n]\n", start)
    assert end != -1, "Missing closing bracket for SUITES in scripts/verify.sh"
    tree = ast.parse(content[start : end + 2])
    assign = tree.body[0]
    assert isinstance(assign, ast.Assign)
    raw = ast.literal_eval(assign.value)
    assert isinstance(raw, list)
    return [tuple(item) for item in raw]


def _build_cdp_driver_script(
    cdp_helper_path: Path,
    chrome_bin: str,
    base_url: str,
    control_url: str,
) -> str:
    """Build ES module script exercising CEHM-FR-02 end-to-end inside headless Chrome."""
    return f"""
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(cdp_helper_path))};

function assert(cond, msg) {{
  if (!cond) {{
    throw new Error('CDP Assertion failed: ' + msg);
  }}
}}

async function waitFor(cdp, expr, label, timeoutMs = 15000) {{
  const deadline = Date.now() + timeoutMs;
  let last = null;
  while (Date.now() < deadline) {{
    last = await cdp.evaluate(expr);
    if (last) return last;
    await new Promise(r => setTimeout(r, 50));
  }}
  throw new Error('Timed out waiting for: ' + label + ' (last=' + JSON.stringify(last) + ')');
}}

async function clickPoint(cdp, box, label) {{
  assert(box && box.width > 0 && box.height > 0, 'Invisible target: ' + label);
  const x = box.x;
  const y = box.y;
  // Omit mouseMoved: on macOS headless Chrome, mouseMoved after Escape stalls ~5s per dispatch.
  await cdp.send('Input.dispatchMouseEvent', {{ type: 'mousePressed', x, y, button: 'left', clickCount: 1 }});
  await cdp.send('Input.dispatchMouseEvent', {{ type: 'mouseReleased', x, y, button: 'left', clickCount: 1 }});
}}

async function clickSelector(cdp, selector, label) {{
  const box = await cdp.evaluate(`(() => {{
    const el = document.querySelector(${{JSON.stringify(selector)}});
    if (!el) return null;
    el.scrollIntoView({{ block: 'center', inline: 'center' }});
    const r = el.getBoundingClientRect();
    return {{ x: r.left + r.width / 2, y: r.top + r.height / 2, width: r.width, height: r.height }};
  }})()`);
  await clickPoint(cdp, box, label || selector);
}}

async function clickRoadmapRowCell(cdp, slug) {{
  const box = await cdp.evaluate(`(() => {{
    const row = document.querySelector('tr.roadmap-epic-row[data-epic-slug="' + ${{JSON.stringify(slug)}} + '"]');
    if (!row) return null;
    const cell = Array.from(row.querySelectorAll('td')).find(td => !td.querySelector('select,button,a,input')) || row.querySelector('td');
    if (!cell) return null;
    cell.scrollIntoView({{ block: 'center', inline: 'center' }});
    const r = cell.getBoundingClientRect();
    return {{ x: r.left + Math.min(24, r.width / 2), y: r.top + r.height / 2, width: r.width, height: r.height }};
  }})()`);
  await clickPoint(cdp, box, 'roadmap row ' + slug);
}}

async function pressEscape(cdp) {{
  await cdp.send('Input.dispatchKeyEvent', {{
    type: 'rawKeyDown',
    key: 'Escape',
    code: 'Escape',
    windowsVirtualKeyCode: 27,
    nativeVirtualKeyCode: 27,
  }});
  await cdp.send('Input.dispatchKeyEvent', {{
    type: 'keyUp',
    key: 'Escape',
    code: 'Escape',
    windowsVirtualKeyCode: 27,
    nativeVirtualKeyCode: 27,
  }});
}}

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Emulation.setDeviceMetricsOverride', {{
    width: 1440,
    height: 960,
    deviceScaleFactor: 1,
    mobile: false,
  }});
  await cdp.send('Page.navigate', {{ url: {json.dumps(base_url)} }});

  await waitFor(cdp, `(() => {{
    const sec2 = document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools');
    const doneRow = document.querySelector('tr.roadmap-epic-row[data-epic-slug="done_epic"]');
    const inProgRow = document.querySelector('tr.roadmap-epic-row[data-epic-slug="in_prog_epic"]');
    const backlogRow = document.querySelector('tr.roadmap-epic-row[data-epic-slug="backlog_epic"]');
    return Boolean(
      sec2 && sec2.textContent.includes('in_prog_epic') &&
      doneRow && inProgRow && backlogRow
    );
  }})()`, 'initial dashboard hydration with all 3 epics');

  const section2TextBefore = await cdp.evaluate(
    `document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').textContent`
  );
  assert(section2TextBefore.includes('in_prog_epic'), 'Section II should render in_prog_epic');

  // 1. Open done_epic history modal via real mouse click on Roadmap row
  await clickRoadmapRowCell(cdp, 'done_epic');
  await waitFor(cdp, `(() => {{
    const modal = document.getElementById('modal-epic-history');
    const title = document.getElementById('epic-history-title');
    const stages = document.querySelectorAll('#epic-history-stepper [data-stage-id]');
    return Boolean(
      modal && modal.style.display === 'flex' &&
      title && title.textContent.includes('done_epic') &&
      stages.length === 6 &&
      document.querySelectorAll('#epic-history-body [data-timeline-filter]').length === 5
    );
  }})()`, 'done_epic modal loaded with 6-stage stepper');

  const openModalState = await cdp.evaluate(`(() => ({{
    display: document.getElementById('modal-epic-history').style.display,
    overflow: document.body.style.overflow,
    stageCount: document.querySelectorAll('#epic-history-stepper [data-stage-id]').length,
    statusText: document.getElementById('epic-history-status-badge').textContent.trim(),
    section2Text: document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').textContent,
  }}))()`);
  assert(openModalState.display === 'flex', 'Modal must display flex');
  assert(openModalState.overflow === 'hidden', 'Body scroll must lock when modal opens');
  assert(openModalState.stageCount === 6, '6-stage stepper required');
  assert(openModalState.section2Text.includes('in_prog_epic'), 'Section II underneath must stay in_prog_epic');

  // 2. Filter Timeline & Step Logs across All, Gates, Steps, Activity, Evidence
  const filterCounts = {{}};
  for (const key of ['all', 'gate', 'step', 'activity', 'evidence']) {{
    await clickSelector(cdp, `#epic-history-body button[data-timeline-filter="${{key}}"]`, 'filter ' + key);
    await waitFor(cdp, `(() => {{
      const btn = document.querySelector('#epic-history-body button[data-timeline-filter="${{key}}"]');
      return Boolean(btn && btn.classList.contains('active'));
    }})()`, 'active filter ' + key);
    const items = await cdp.evaluate(`Array.from(document.querySelectorAll('#epic-history-body .epic-history-card')).map(el => ({{
      category: el.getAttribute('data-timeline-category') || '',
      text: el.textContent || ''
    }}))`);
    filterCounts[key] = items.length;
    assert(items.length >= 1, 'Expected timeline items for filter ' + key);
    if (key !== 'all') {{
      assert(items.every(i => i.category === key), 'Mismatched timeline category under filter ' + key);
    }}
    if (key === 'step') {{
      assert(items.length === 25, 'Expected all 25 archived step events, got ' + items.length);
      const joined = items.map(i => i.text).join('\\n');
      assert(joined.includes('Archived step event 01 executed'), 'Missing archived step event 01');
      assert(joined.includes('Archived step event 25 executed'), 'Missing archived step event 25');
    }}
  }}
  assert(filterCounts.all > 25, 'All filter must exceed 25 combined events');
  await clickSelector(cdp, '#epic-history-body button[data-timeline-filter="all"]', 'restore all filter');

  // 3. Switch to Tasks & Evidence and expand verification rows
  await clickSelector(cdp, '#epic-history-tabs button[data-history-tab="tasks"]', 'tasks tab');
  await waitFor(cdp, `document.querySelectorAll('#epic-history-body .epic-history-card[data-task-id]').length === 11`, '11 task cards rendered');
  const firstTaskToggle = 'button[data-evidence-task-id="task_01_fixture_01"]';
  const beforeExpandText = await cdp.evaluate(`document.getElementById('epic-history-body').textContent`);
  assert(!beforeExpandText.includes('V2 GREEN verification output_tail for task 01'), 'Details should start collapsed');
  await clickSelector(cdp, firstTaskToggle, 'expand task_01 evidence');
  await waitFor(cdp, `document.getElementById('epic-history-body').textContent.includes('V2 GREEN verification output_tail for task 01')`, 'expanded verification output_tail visible');
  const expandedTaskText = await cdp.evaluate(`document.getElementById('epic-history-body').textContent`);
  assert(expandedTaskText.includes('PASS'), 'Expanded verification must show PASS status');

  // 4. Switch directly between Principal Review and Cross-Model Review, toggling Round 1 <-> Round 2 in-place
  await clickSelector(cdp, '#epic-history-tabs button[data-history-tab="principal"]', 'principal tab');
  await waitFor(cdp, `document.getElementById('epic-history-body').textContent.includes('Round 1 Principal important finding')`, 'principal round 1 initially visible');
  await clickSelector(cdp, '#epic-history-body button[data-review-round="2"]', 'principal round 2');
  await waitFor(cdp, `document.getElementById('epic-history-body').textContent.includes('Round 2 Principal minor check')`, 'principal round 2 findings visible');
  await clickSelector(cdp, '#epic-history-body button[data-review-round="1"]', 'principal round 1');
  await waitFor(cdp, `document.getElementById('epic-history-body').textContent.includes('Round 1 Principal important finding')`, 'principal round 1 restored');

  await clickSelector(cdp, '#epic-history-tabs button[data-history-tab="cross_model"]', 'cross_model tab');
  await waitFor(cdp, `document.getElementById('epic-history-body').textContent.includes('Round 1 Cross-Model important finding')`, 'cross-model round 1 initially visible');
  await clickSelector(cdp, '#epic-history-body button[data-review-round="2"]', 'cross_model round 2');
  await waitFor(cdp, `document.getElementById('epic-history-body').textContent.includes('Round 2 Cross-Model minor polish')`, 'cross-model round 2 findings visible');
  await clickSelector(cdp, '#epic-history-body button[data-review-round="1"]', 'cross_model round 1');
  await waitFor(cdp, `document.getElementById('epic-history-body').textContent.includes('Round 1 Cross-Model important finding')`, 'cross-model round 1 restored');

  const crossModalDisplay = await cdp.evaluate(`getComputedStyle(document.getElementById('modal-cross-review')).display`);
  assert(crossModalDisplay === 'none', '#modal-cross-review must remain hidden during in-place review switching');

  // 5. Escape closes modal and restores body overflow
  await pressEscape(cdp);
  await waitFor(cdp, `document.getElementById('modal-epic-history').style.display === 'none'`, 'Escape closed modal');
  const overflowAfterEsc = await cdp.evaluate(`document.body.style.overflow`);
  assert(overflowAfterEsc === '', 'Body overflow must reset after Escape close');

  // 6. Inline PIC select inside Roadmap row stops propagation and persists PIC
  const picSelectDispatched = await cdp.evaluate(`(() => {{
    const sel = document.querySelector('tr.roadmap-epic-row[data-epic-slug="done_epic"] select.select-pic-roadmap');
    if (!sel) return false;
    sel.focus();
    sel.dispatchEvent(new MouseEvent('mousedown', {{ bubbles: true, cancelable: true }}));
    sel.dispatchEvent(new MouseEvent('click', {{ bubbles: true, cancelable: true }}));
    return true;
  }})()`);
  assert(picSelectDispatched, 'Missing inline PIC select for done_epic');
  await new Promise(r => setTimeout(r, 150));
  const modalAfterPicClick = await cdp.evaluate(`document.getElementById('modal-epic-history').style.display`);
  assert(modalAfterPicClick !== 'flex', 'Clicking inline PIC select must not open history modal');
  await cdp.evaluate(`(() => {{
    const sel = document.querySelector('tr.roadmap-epic-row[data-epic-slug="done_epic"] select.select-pic-roadmap');
    sel.value = 'danhdue';
    sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
    sel.blur();
  }})()`);
  await new Promise(r => setTimeout(r, 250));
  const picAfterChange = await cdp.evaluate(`(() => ({{
    modalDisplay: document.getElementById('modal-epic-history').style.display,
    picValue: document.querySelector('tr.roadmap-epic-row[data-epic-slug="done_epic"] select.select-pic-roadmap')?.value || '',
  }}))()`);
  assert(picAfterChange.modalDisplay !== 'flex', 'Changing inline PIC select must not open history modal');
  assert(picAfterChange.picValue === 'danhdue', 'Changing inline PIC select must update PIC to danhdue');

  // 7. Open backlog_epic and verify clean empty history states without crashing, then close with X
  await clickRoadmapRowCell(cdp, 'backlog_epic');
  await waitFor(cdp, `(() => {{
    const modal = document.getElementById('modal-epic-history');
    const title = document.getElementById('epic-history-title');
    return Boolean(modal && modal.style.display === 'flex' && title && title.textContent.includes('backlog_epic') && !document.getElementById('epic-history-body').textContent.includes('Loading epic history...'));
  }})()`, 'backlog_epic modal loaded');
  for (const tabKey of ['tasks', 'principal', 'cross_model', 'timeline']) {{
    await clickSelector(cdp, `#epic-history-tabs button[data-history-tab="${{tabKey}}"]`, 'backlog tab ' + tabKey);
    await waitFor(cdp, `document.getElementById('epic-history-body').textContent.trim().length > 0`, 'backlog empty state text ' + tabKey);
  }}
  await clickSelector(cdp, '#modal-epic-history .modal-close-btn', 'close button X');
  await waitFor(cdp, `document.getElementById('modal-epic-history').style.display === 'none'`, 'X button closed backlog modal');
  assert(await cdp.evaluate(`document.body.style.overflow`) === '', 'Body overflow must reset after X close');

  // 8. Inject HTTP 500 on /api/epic/history -> verify error banner & Retry recovery
  const armRes = await fetch({json.dumps(control_url)} + '/arm-500', {{ method: 'POST' }});
  assert(armRes.ok, 'Failed to arm 500 injection');
  await clickRoadmapRowCell(cdp, 'done_epic');
  await waitFor(cdp, `(() => {{
    const banner = document.getElementById('epic-history-error-banner');
    const retry = document.getElementById('epic-history-retry-btn');
    return Boolean(banner && getComputedStyle(banner).display !== 'none' && retry && getComputedStyle(retry).display !== 'none');
  }})()`, 'HTTP 500 error banner + retry button visible');
  const bannerText = await cdp.evaluate(`document.getElementById('epic-history-error-text').textContent`);
  assert(bannerText.includes('500') || bannerText.includes('Simulated'), 'Error banner text should describe failure: ' + bannerText);

  await clickSelector(cdp, '#epic-history-retry-btn', 'retry epic history button');
  await waitFor(cdp, `(() => {{
    const banner = document.getElementById('epic-history-error-banner');
    const title = document.getElementById('epic-history-title');
    const cards = document.querySelectorAll('#epic-history-body .epic-history-card');
    return Boolean(
      banner && getComputedStyle(banner).display === 'none' &&
      title && title.textContent.includes('done_epic') &&
      cards.length > 25
    );
  }})()`, 'Retry recovered modal cleanly');

  await pressEscape(cdp);
  await waitFor(cdp, `document.getElementById('modal-epic-history').style.display === 'none'`, 'Final Escape closed modal');

  const result = {{
    ok: true,
    filterCounts,
    consoleErrors: cdp.consoleErrors,
    runtimeExceptions: cdp.runtimeExceptions,
  }};
  console.log(JSON.stringify(result));
}} finally {{
  await cdp.close();
}}
"""


def _run_e2e_cdp_flow(
    tmp_path: Path,
    chrome_bin: str,
    ws_root: Path,
) -> dict[str, Any]:
    """Start real TasksServer + control server, drive headless Chrome CDP, return result."""
    server_state: dict[str, bool] = {"fail_next_history_once": False}
    port = find_available_port(19100)
    pid_file = tmp_path / "agy_tasks_server.pid"

    server = TasksServer(
        host="127.0.0.1",
        port=port,
        workspace_root=ws_root,
        pid_file=pid_file,
    )
    server.RequestHandlerClass = _ControllableTasksHandler
    server.cehm_test_state = server_state  # type: ignore[attr-defined]
    actual_port = int(server.server_address[1])
    control_port = find_available_port(actual_port + 1)
    control_server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", control_port),
        _make_control_handler(server_state),
    )

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    control_thread = threading.Thread(target=control_server.serve_forever, daemon=True)
    server_thread.start()
    control_thread.start()
    try:
        cdp_helper_path = tmp_path / "cdp_helper.mjs"
        cdp_helper_path.write_text(_NODE_CDP_HELPER, encoding="utf-8")
        driver_script = _build_cdp_driver_script(
            cdp_helper_path=cdp_helper_path,
            chrome_bin=chrome_bin,
            base_url=f"http://127.0.0.1:{actual_port}/",
            control_url=f"http://127.0.0.1:{control_port}",
        )
        return _run_node_script(driver_script, timeout=90)
    finally:
        with contextlib.suppress(Exception):
            control_server.shutdown()
            control_server.server_close()
        with contextlib.suppress(Exception):
            server.shutdown()
            server.server_close()


def test_cehm_fr_02_end_to_end_chrome_cdp_history_modal_workflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """BDD CEHM-FR-02: Verify live TasksServer + headless Chrome CDP workflow and verify.sh registration."""
    assert shutil.which("node"), "Node.js is required for headless Chrome CDP tests"
    chrome_bin = _resolve_chrome_binary()
    assert chrome_bin, (
        "Google Chrome / Chromium binary required for headless Chrome CDP"
    )

    import tasks_server  # type: ignore[import-not-found]

    monkeypatch.setattr(
        check_tasks,
        "discover_antigravity_profiles",
        lambda: ["phungthuy8901", "danhdue", "brother", "tess"],
    )
    monkeypatch.setattr(
        tasks_server,
        "discover_antigravity_profiles",
        lambda: ["phungthuy8901", "danhdue", "brother", "tess"],
    )

    ws_root = tmp_path / "workspace"
    repo_dir = ws_root / "ai-agent-tools"
    _init_git_repo(repo_dir)
    _seed_done_epic(repo_dir)
    _seed_in_prog_and_backlog_epics(repo_dir)

    result = _run_e2e_cdp_flow(tmp_path, chrome_bin, ws_root)
    assert result["ok"] is True
    assert result["consoleErrors"] == [], f"Console errors: {result['consoleErrors']}"
    assert result["runtimeExceptions"] == [], (
        f"Runtime exceptions: {result['runtimeExceptions']}"
    )

    # Confirm inline PIC mutation persisted cleanly to done_epic HLD on disk
    deadline = time.monotonic() + 3.0
    hld_path = repo_dir / ".devtool" / "epic" / "done_epic" / "done_epic.en.md"
    while time.monotonic() < deadline:
        if "danhdue" in hld_path.read_text(encoding="utf-8"):
            break
        time.sleep(0.05)
    assert "danhdue" in hld_path.read_text(encoding="utf-8")

    # Assert scripts/verify.sh registers all 4 CEHM pytest suites
    suites = _extract_verify_suites(REPO_ROOT / "scripts" / "verify.sh")
    registered = {
        path: (section, mode, skip) for section, mode, path, _timeout, skip in suites
    }
    for suite_path in CEHM_VERIFY_SUITES:
        assert suite_path in registered, f"Missing verify.sh registration: {suite_path}"
        section, mode, skip = registered[suite_path]
        assert section == "20", (
            f"Expected section '20' for {suite_path}, got {section!r}"
        )
        assert mode == "pytest", f"Expected pytest mode for {suite_path}, got {mode!r}"
        assert skip is False, f"Expected active suite (skip=False) for {suite_path}"
