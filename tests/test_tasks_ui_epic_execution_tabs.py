"""Unit, API, and Headless Chrome E2E tests for Section II Execution Tabs (Doing/Pending/Cancelled)
and Kanban Dashboard status filtering.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts"
CHECK_TASKS_SCRIPTS = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
for p in (str(SCRIPTS_ROOT), str(CHECK_TASKS_SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import _state_envelope  # type: ignore[import-not-found]  # noqa: E402
import check_tasks  # type: ignore[import-not-found]  # noqa: E402
from tasks_server import (  # type: ignore[import-not-found]  # noqa: E402
    TasksHandler,
    TasksServer,
    find_available_port,
    set_epic_execution_state_for_repo,
)
from tests.test_rsdh_tasks_dashboard_ui import (  # noqa: E402
    _NODE_CDP_HELPER,
    _resolve_chrome_binary,
    _run_node_script,
)


def _init_git_repo(repo_dir: Path) -> Path:
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    (repo_dir / "README.md").write_text("# Demo Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo_dir, check=True)
    return repo_dir


def _seed_demo_workspace(ws_root: Path) -> Path:
    """Create a workspace with 2 active epics: one handed-off (handoff_epic) and one pre-handoff (stage1_epic)."""
    repo = _init_git_repo(ws_root / "ai-agent-tools")
    devtool = repo / ".devtool"

    # Epic 1: handed-off epic with handoff.md + 2 tasks
    ep1 = devtool / "epic" / "handoff_epic"
    ep1.mkdir(parents=True, exist_ok=True)
    (ep1 / "handoff_epic.md").write_text(
        "# Epic: handoff_epic\n\n- **Status**: In Progress\n- **PIC**: danhdue\n",
        encoding="utf-8",
    )
    (ep1 / "handoff.md").write_text("# Handoff\nPackaged.\n", encoding="utf-8")

    # Epic 2: in-progress epic BEFORE handoff.md + 1 task
    ep2 = devtool / "epic" / "stage1_epic"
    ep2.mkdir(parents=True, exist_ok=True)
    (ep2 / "stage1_epic.md").write_text(
        "# Epic: stage1_epic\n\n- **Status**: In Progress\n- **PIC**: danhdue\n",
        encoding="utf-8",
    )

    # Seed tasks in .devtool/features/
    features = devtool / "features"
    features.mkdir(parents=True, exist_ok=True)
    (features / "task_01_handoff.md").write_text(
        "---\nid: task_01_handoff\nepic: handoff_epic\nstatus: in-progress\npriority: P0\ntitle: Handoff Task 1\n---\n# Handoff Task 1\n",
        encoding="utf-8",
    )
    (features / "task_02_handoff.md").write_text(
        "---\nid: task_02_handoff\nepic: handoff_epic\nstatus: todo\npriority: P1\ntitle: Handoff Task 2\n---\n# Handoff Task 2\n",
        encoding="utf-8",
    )
    (features / "task_03_stage1.md").write_text(
        "---\nid: task_03_stage1\nepic: stage1_epic\nstatus: backlog\npriority: P1\ntitle: Stage 1 Task\n---\n# Stage 1 Task\n",
        encoding="utf-8",
    )

    # Seed Gate 1 & Gate 2 in GATE_LEDGER.md + active pending decision on handoff_epic
    (devtool / "GATE_LEDGER.md").write_text(
        "| Timestamp | Epic | Gate | Commit | Approved Scope | Deviations / Notes | Approver |\n"
        "|---|---|---|---|---|---|---|\n"
        "| 2026-11-26T00:00:00Z | handoff_epic | 1 | abc1234 | Spec | | developer |\n"
        "| 2026-11-26T00:01:00Z | handoff_epic | 2 | abc1234 | HLD | | developer |\n"
        "| 2026-11-26T00:02:00Z | stage1_epic | 1 | abc1234 | Spec | | developer |\n",
        encoding="utf-8",
    )
    _state_envelope.record_pending_decision(
        repo,
        "handoff_epic",
        "Confirm execution mode",
        kind="gate_2",
        stage="Stage 2 Exit (Handoff)",
    )
    return repo


def test_state_envelope_execution_state_and_harvester_propagation(tmp_path: Path) -> None:
    """State envelope persists pending/cancelled + reason, clears pending_decision, and harvester propagates counts."""
    repo = _seed_demo_workspace(tmp_path)

    with pytest.raises(ValueError, match="Reason is required"):
        _state_envelope.set_epic_execution_state(repo, "handoff_epic", "pending", reason="   ")

    with pytest.raises(ValueError, match="Invalid execution state"):
        _state_envelope.set_epic_execution_state(repo, "handoff_epic", "archived", reason="x")

    _state_envelope.set_epic_execution_state(
        repo, "handoff_epic", "pending", reason="Waiting for API contract"
    )
    states = _state_envelope.read_epic_execution_states(repo)
    assert states["handoff_epic"]["state"] == "pending"
    assert states["handoff_epic"]["reason"] == "Waiting for API contract"

    meta = check_tasks.scan_repo(repo)
    assert meta.epics_summary is not None
    ep_map = {e["slug"]: e for e in meta.epics_summary.epics}
    assert ep_map["handoff_epic"]["execution_state"] == "pending"
    assert ep_map["handoff_epic"]["execution_state_reason"] == "Waiting for API contract"
    assert ep_map["handoff_epic"]["is_action_required"] is False
    assert ep_map["stage1_epic"]["execution_state"] == "doing"
    assert meta.epics_summary.doing_count == 1
    assert meta.epics_summary.in_progress == 1
    assert meta.epics_summary.pending_count == 1
    assert meta.epics_summary.cancelled_count == 0
    assert meta.epics_summary.abandoned == 0

    # Resume back to doing removes the override
    _state_envelope.set_epic_execution_state(repo, "handoff_epic", "doing")
    assert _state_envelope.read_epic_execution_states(repo) == {}
    meta_resumed = check_tasks.scan_repo(repo)
    assert meta_resumed.epics_summary is not None
    assert meta_resumed.epics_summary.doing_count == 2
    assert meta_resumed.epics_summary.pending_count == 0


def test_tasks_server_execution_state_api_validation(tmp_path: Path) -> None:
    """POST /api/epic/execution-state validates inputs and persists state cleanly."""
    _seed_demo_workspace(tmp_path)

    with pytest.raises(ValueError, match="Reason is required"):
        set_epic_execution_state_for_repo(tmp_path, "ai-agent-tools", "handoff_epic", "cancelled", "")
    with pytest.raises(ValueError, match="Invalid repository name"):
        set_epic_execution_state_for_repo(tmp_path, "../escape", "handoff_epic", "pending", "bad")

    port = find_available_port(19720)
    server = TasksServer("127.0.0.1", port, workspace_root=tmp_path)
    actual_port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{actual_port}"

        def _post(body: dict[str, str]) -> tuple[int, dict[str, object]]:
            req = urllib.request.Request(
                f"{base_url}/api/epic/execution-state",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.status, json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as err:
                return err.code, json.loads(err.read().decode("utf-8"))

        rc_bad, data_bad = _post(
            {"repo": "ai-agent-tools", "epic": "handoff_epic", "state": "pending", "reason": ""}
        )
        assert rc_bad == 400
        assert data_bad["status"] == "error"

        rc_ok, data_ok = _post(
            {
                "repo": "ai-agent-tools",
                "epic": "handoff_epic",
                "state": "pending",
                "reason": "Blocked by external vendor",
            }
        )
        assert rc_ok == 200
        assert data_ok["state"] == "pending"
        assert data_ok["reason"] == "Blocked by external vendor"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_remove_worktree_clean_and_preserve_dirty(tmp_path: Path) -> None:
    """remove_worktree=True safely removes clean worktrees & slots while preserving git branches, epic docs, and dirty worktrees."""
    repo = _seed_demo_workspace(tmp_path)
    # Create clean epic worktree + clean slot-1 for handoff_epic
    clean_wt = repo / ".worktrees" / "handoff_epic"
    clean_slot = repo / ".worktrees" / "handoff_epic-slot-1"
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", "epic/handoff-epic", str(clean_wt)],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "worktree", "add", "-q", "--detach", str(clean_slot), "epic/handoff-epic"],
        cwd=repo,
        check=True,
    )

    # Create dirty worktree for stage1_epic
    dirty_wt = repo / ".worktrees" / "stage1_epic"
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", "epic/stage1-epic", str(dirty_wt)],
        cwd=repo,
        check=True,
    )
    (dirty_wt / "uncommitted_wip.txt").write_text("WIP code\n", encoding="utf-8")

    # 1. Clean worktree + slot removed on Pending with remove_worktree=True; branch & epic docs preserved
    res_clean = set_epic_execution_state_for_repo(
        tmp_path,
        "ai-agent-tools",
        "handoff_epic",
        "pending",
        reason="Pause to free disk space",
        remove_worktree=True,
    )
    assert res_clean["status"] == "ok"
    assert len(res_clean["worktree_cleanup"]["removed"]) == 2
    assert res_clean["worktree_cleanup"]["skipped_dirty"] == []
    assert not clean_wt.exists()
    assert not clean_slot.exists()
    assert (repo / ".devtool" / "epic" / "handoff_epic" / "handoff_epic.md").is_file()
    branch_check = subprocess.run(
        ["git", "rev-parse", "--verify", "refs/heads/epic/handoff-epic"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    assert branch_check.returncode == 0

    # 2. Dirty worktree preserved safely on Cancel with remove_worktree=True
    res_dirty = set_epic_execution_state_for_repo(
        tmp_path,
        "ai-agent-tools",
        "stage1_epic",
        "cancelled",
        reason="Shelve epic",
        remove_worktree=True,
    )
    assert res_dirty["status"] == "ok"
    assert res_dirty["worktree_cleanup"]["removed"] == []
    assert len(res_dirty["worktree_cleanup"]["skipped_dirty"]) == 1
    assert dirty_wt.is_dir()
    assert (dirty_wt / "uncommitted_wip.txt").is_file()


def test_e2e_headless_chrome_execution_tabs_modal_and_kanban_filter(
    tmp_path: Path,
) -> None:
    """Real Headless Chrome E2E verifying Section II 3 tabs, Pending/Cancel reason modal, Resume, Kanban filters, and reload persistence."""
    chrome_bin = _resolve_chrome_binary()
    if not chrome_bin:
        pytest.skip("Headless Chrome binary not available on this host")

    _seed_demo_workspace(tmp_path)
    port = find_available_port(19760)
    server = TasksServer("127.0.0.1", port, workspace_root=tmp_path)
    actual_port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{actual_port}"
        script = f"""
{_NODE_CDP_HELPER}

function assert(cond, msg) {{
  if (!cond) throw new Error('ASSERTION FAILED: ' + msg);
}}

async function waitFor(cdp, expr, label, timeoutMs = 15000) {{
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {{
    const val = await cdp.evaluate(expr);
    if (val) return val;
    await new Promise((r) => setTimeout(r, 120));
  }}
  throw new Error('Timed out waiting for: ' + label);
}}

async function run() {{
  const cdp = await launchHeadlessChromeCdp({json.dumps(str(chrome_bin))});
  try {{
    await cdp.send('Page.navigate', {{ url: {json.dumps(base_url)} }});

    // 1. Wait for initial dashboard render showing both Doing epics (including pre-handoff stage1_epic)
    await waitFor(cdp, `(() => {{
      const w = document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools');
      if (!w) return false;
      const cards = w.querySelectorAll('.epic-execution-item');
      return cards.length === 2
        && w.textContent.includes('handoff_epic')
        && w.textContent.includes('stage1_epic');
    }})()`, 'Initial Doing tab renders both handoff_epic and stage1_epic');

    const initialState = await cdp.evaluate(`(() => ({{
      doingTab: document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools button[data-exec-tab="doing"]')?.textContent?.trim(),
      pendingTab: document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools button[data-exec-tab="pending"]')?.textContent?.trim(),
      cancelledTab: document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools button[data-exec-tab="cancelled"]')?.textContent?.trim(),
      pendingBtns: document.querySelectorAll('#tier2-execution-epics-wrapper-ai-agent-tools button[data-epic-action="pending"]').length,
      cancelBtns: document.querySelectorAll('#tier2-execution-epics-wrapper-ai-agent-tools button[data-epic-action="cancelled"]').length,
      kanbanCards: document.querySelectorAll('#kanban-dashboard-wrapper-ai-agent-tools .kanban-task-card').length,
    }}))()`);
    assert(initialState.doingTab.includes('2'), 'Doing tab should show 2: ' + initialState.doingTab);
    assert(initialState.pendingTab.includes('0'), 'Pending tab should show 0: ' + initialState.pendingTab);
    assert(initialState.cancelledTab.includes('0'), 'Cancelled tab should show 0: ' + initialState.cancelledTab);
    assert(initialState.pendingBtns === 2, 'Expected 2 Pending buttons on Doing cards');
    assert(initialState.cancelBtns === 2, 'Expected 2 Cancel buttons on Doing cards');
    assert(initialState.kanbanCards === 3, 'Kanban Doing default should show all 3 tasks');

    // 1b. Switch to empty Pending tab and verify zero layout collapse (panel height preserved)
    const doingPanelHeight = await cdp.evaluate(`Math.round(document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools .exec-tab-panel').getBoundingClientRect().height)`);
    await cdp.evaluate(`document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools button[data-exec-tab="pending"]').click()`);
    await waitFor(cdp, `Boolean(document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools [data-exec-empty="pending"]'))`, 'Empty Pending placeholder renders');
    const emptyPendingHeight = await cdp.evaluate(`Math.round(document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools .exec-tab-panel').getBoundingClientRect().height)`);
    assert(emptyPendingHeight >= doingPanelHeight, `Empty Pending panel collapsed (${{emptyPendingHeight}} < ${{doingPanelHeight}})`);
    await cdp.evaluate(`document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools button[data-exec-tab="doing"]').click()`);
    await waitFor(cdp, `document.querySelectorAll('#tier2-execution-epics-wrapper-ai-agent-tools .epic-execution-item').length === 2`, 'Doing tab restored');

    // 1c. Switch Kanban to empty Pending filter and verify Kanban board shell height stays stable
    const doingKanbanHeight = await cdp.evaluate(`Math.round(document.querySelector('#kanban-dashboard-wrapper-ai-agent-tools .kanban-board-shell').getBoundingClientRect().height)`);
    await cdp.evaluate(`document.querySelector('#kanban-dashboard-wrapper-ai-agent-tools button[data-kanban-exec-filter="pending"]').click()`);
    await waitFor(cdp, `document.querySelectorAll('#kanban-dashboard-wrapper-ai-agent-tools .kanban-task-card').length === 0`, 'Empty Kanban Pending view renders');
    const emptyKanbanHeight = await cdp.evaluate(`Math.round(document.querySelector('#kanban-dashboard-wrapper-ai-agent-tools .kanban-board-shell').getBoundingClientRect().height)`);
    assert(emptyKanbanHeight >= doingKanbanHeight, `Kanban shell collapsed (${{emptyKanbanHeight}} < ${{doingKanbanHeight}})`);
    await cdp.evaluate(`document.querySelector('#kanban-dashboard-wrapper-ai-agent-tools button[data-kanban-exec-filter="doing"]').click()`);
    await waitFor(cdp, `document.querySelectorAll('#kanban-dashboard-wrapper-ai-agent-tools .kanban-task-card').length === 3`, 'Kanban Doing view restored');

    // 2. Click Pending on handoff_epic -> modal opens -> empty submit shows validation error
    await cdp.evaluate(`document.querySelector('.epic-execution-item[data-epic-slug="handoff_epic"] button[data-epic-action="pending"]').click()`);
    await waitFor(cdp, `document.getElementById('modal-epic-state-confirm').style.display === 'flex'`, 'Pending modal opens');

    await cdp.evaluate(`document.getElementById('epic-state-modal-submit-btn').click()`);
    await waitFor(cdp, `document.getElementById('epic-state-reason-error').style.display === 'block'`, 'Empty reason error shown');

    // 3. Fill reason and submit -> handoff_epic moves to Pending & disappears from Doing Kanban
    await cdp.evaluate(`(() => {{
      const ta = document.getElementById('epic-state-reason-input');
      ta.value = 'Waiting for upstream API spec';
      ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
      document.getElementById('epic-state-modal-submit-btn').click();
    }})()`);
    await waitFor(cdp, `document.getElementById('modal-epic-state-confirm').style.display === 'none'`, 'Modal closes after submit');
    await waitFor(cdp, `(() => {{
      const w = document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools');
      const kw = document.getElementById('kanban-dashboard-wrapper-ai-agent-tools');
      return w.querySelectorAll('.epic-execution-item').length === 1
        && !w.textContent.includes('handoff_epic')
        && kw.querySelectorAll('.kanban-task-card').length === 1;
    }})()`, 'handoff_epic leaves Doing and Doing Kanban');

    // 4. Switch Section II to Pending tab -> verify reason banner + Resume button
    await cdp.evaluate(`document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools button[data-exec-tab="pending"]').click()`);
    await waitFor(cdp, `(() => {{
      const w = document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools');
      return w.textContent.includes('handoff_epic')
        && w.textContent.includes('Waiting for upstream API spec')
        && w.querySelectorAll('button[data-epic-action="resume"]').length === 1;
    }})()`, 'Pending tab displays handoff_epic with reason and Resume button');

    // 5. Switch Kanban sidebar filter to Pending -> verify handoff_epic's 2 tasks appear
    await cdp.evaluate(`document.querySelector('#kanban-dashboard-wrapper-ai-agent-tools button[data-kanban-exec-filter="pending"]').click()`);
    await waitFor(cdp, `(() => {{
      const kw = document.getElementById('kanban-dashboard-wrapper-ai-agent-tools');
      return kw.querySelectorAll('.kanban-task-card').length === 2
        && kw.textContent.includes('Handoff Task 1')
        && kw.textContent.includes('Handoff Task 2');
    }})()`, 'Kanban Pending filter shows handoff_epic tasks');

    // 6. Switch Section II back to Doing and Cancel stage1_epic with reason
    await cdp.evaluate(`document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools button[data-exec-tab="doing"]').click()`);
    await waitFor(cdp, `Boolean(document.querySelector('.epic-execution-item[data-epic-slug="stage1_epic"] button[data-epic-action="cancelled"]'))`, 'stage1_epic Cancel button visible');
    await cdp.evaluate(`document.querySelector('.epic-execution-item[data-epic-slug="stage1_epic"] button[data-epic-action="cancelled"]').click()`);
    await waitFor(cdp, `document.getElementById('modal-epic-state-confirm').style.display === 'flex'`, 'Cancel modal opens');
    await cdp.evaluate(`(() => {{
      const ta = document.getElementById('epic-state-reason-input');
      ta.value = 'Superseded by v2 architecture';
      ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
      document.getElementById('epic-state-modal-submit-btn').click();
    }})()`);
    await waitFor(cdp, `document.getElementById('modal-epic-state-confirm').style.display === 'none'`, 'Cancel modal closes');

    // 7. Verify Cancelled tab + Kanban Cancelled filter
    await cdp.evaluate(`document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools button[data-exec-tab="cancelled"]').click()`);
    await waitFor(cdp, `(() => {{
      const w = document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools');
      return w.textContent.includes('stage1_epic')
        && w.textContent.includes('Superseded by v2 architecture')
        && w.querySelectorAll('button[data-epic-action="resume"]').length === 1;
    }})()`, 'Cancelled tab displays stage1_epic with reason and Resume button');

    await cdp.evaluate(`document.querySelector('#kanban-dashboard-wrapper-ai-agent-tools button[data-kanban-exec-filter="cancelled"]').click()`);
    await waitFor(cdp, `(() => {{
      const kw = document.getElementById('kanban-dashboard-wrapper-ai-agent-tools');
      return kw.querySelectorAll('.kanban-task-card').length === 1
        && kw.textContent.includes('Stage 1 Task');
    }})()`, 'Kanban Cancelled filter shows stage1_epic task');

    // 8. Resume handoff_epic from Pending tab -> returns to Doing + Doing Kanban
    await cdp.evaluate(`document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools button[data-exec-tab="pending"]').click()`);
    await waitFor(cdp, `Boolean(document.querySelector('.epic-execution-item[data-epic-slug="handoff_epic"] button[data-epic-action="resume"]'))`, 'Resume button visible in Pending');
    await cdp.evaluate(`document.querySelector('.epic-execution-item[data-epic-slug="handoff_epic"] button[data-epic-action="resume"]').click()`);
    await waitFor(cdp, `document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools button[data-exec-tab="doing"]').textContent.includes('1')`, 'Doing count increments to 1');

    // 9. Reload page and confirm persistence (handoff_epic in Doing, stage1_epic in Cancelled)
    await cdp.send('Page.reload', {{ ignoreCache: true }});
    await waitFor(cdp, `(() => {{
      const w = document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools');
      const kw = document.getElementById('kanban-dashboard-wrapper-ai-agent-tools');
      const ov = document.getElementById('epics-overview-counts-ai-agent-tools');
      return w && kw && ov
        && w.querySelectorAll('.epic-execution-item').length === 1
        && w.textContent.includes('handoff_epic')
        && w.querySelector('button[data-exec-tab="cancelled"]')?.textContent?.includes('1')
        && kw.querySelectorAll('.kanban-task-card').length === 2
        && ov.querySelector('[data-overview-count="doing"]')?.textContent?.trim() === '1'
        && ov.querySelector('[data-overview-count="pending"]')?.textContent?.trim() === '0'
        && ov.querySelector('[data-overview-count="cancelled"]')?.textContent?.trim() === '1';
    }})()`, 'State persists cleanly across full reload including Epics Overview counts');

    assert(cdp.consoleErrors.length === 0, 'Expected 0 console errors, got: ' + JSON.stringify(cdp.consoleErrors));
    assert(cdp.runtimeExceptions.length === 0, 'Expected 0 runtime exceptions, got: ' + JSON.stringify(cdp.runtimeExceptions));
    console.log(JSON.stringify({{ ok: true }}));
  }} finally {{
    await cdp.close();
  }}
}}

run().catch((err) => {{
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
}});
"""
        result = _run_node_script(script, timeout=45)
        assert result.get("ok") is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
