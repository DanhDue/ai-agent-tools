"""Cross-layer end-to-end integration and regression suite for Task 07.

Covers BDD Scenarios:
- RSDH-HP-09: End-to-end orchestration, envelope sync, 96% dashboard, PIC sync,
  and Chrome CDP modal stack pass together
- RSDH-FR-06: Registered verification suites guard byte budgets, idle false
  positives, and snapshot isolation continuously
"""

from __future__ import annotations

import ast
import contextlib
from datetime import datetime, timedelta, timezone
import http.server
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
from types import ModuleType
from typing import Any
import urllib.request

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEV_IMPL_SCRIPTS = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
QC_SCRIPTS = REPO_ROOT / "skills" / "quality_check" / "resources" / "scripts"
CHECK_TASKS_SCRIPTS = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
QUOTA_DASHBOARD_HTML = (
    REPO_ROOT
    / "skills"
    / "check-quota"
    / "resources"
    / "dashboard"
    / "quota_dashboard.html"
)

RESUME_SCRIPT = SCRIPTS_DIR / "resume_context.py"
ESTIMATE_SCRIPT = SCRIPTS_DIR / "estimate_heartbeat.py"
VERIFY_QC_SCRIPT = QC_SCRIPTS / "verify_polyglot_registry.py"
PACKAGE_SCRIPT = DEV_IMPL_SCRIPTS / "package_epic.py"
RUN_TASK_CHECKS_SCRIPT = DEV_IMPL_SCRIPTS / "run_task_checks.py"
SYNC_TASK_SCRIPT = DEV_IMPL_SCRIPTS / "sync_task_status.py"
POOL_SCRIPT = DEV_IMPL_SCRIPTS / "manage_worker_pool.py"

for _sys_dir in (
    str(SCRIPTS_DIR),
    str(DEV_IMPL_SCRIPTS),
    str(QC_SCRIPTS),
    str(CHECK_TASKS_SCRIPTS),
):
    if _sys_dir not in sys.path:
        sys.path.insert(0, _sys_dir)

from test_check_epic_readiness import build_ready_epic  # type: ignore[import-not-found]  # noqa: E402
import check_tasks  # type: ignore[import-not-found]  # noqa: E402
import tasks_server  # type: ignore[import-not-found]  # noqa: E402

ISOLATED_GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "RSDH Integration",
    "GIT_AUTHOR_EMAIL": "rsdh-int@example.com",
    "GIT_COMMITTER_NAME": "RSDH Integration",
    "GIT_COMMITTER_EMAIL": "rsdh-int@example.com",
}

EXPECTED_EPIC_SUITES = (
    "tests/test_rsdh_state_envelope.py",
    "tests/test_rsdh_heartbeat_quality.py",
    "tests/test_rsdh_orchestration.py",
    "tests/test_rsdh_harvester_and_pic.py",
    "tests/test_rsdh_tasks_dashboard_ui.py",
    "tests/test_rsdh_quota_modal_stack.py",
    "tests/test_runtime_sync_and_dashboard_hardening.py",
)

EXPECTED_NEW_SCRIPTS = (
    "scripts/_state_envelope.py",
    "scripts/estimate_heartbeat.py",
)

_NODE_CDP_HELPER = r"""
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';

export async function launchHeadlessChromeCdp(chromeBin) {
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'rsdh-e2e-cdp-'));
  const chrome = spawn(
    chromeBin,
    [
      '--headless=new',
      '--disable-gpu',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-background-networking',
      '--remote-debugging-port=0',
      `--user-data-dir=${userDataDir}`,
      'about:blank',
    ],
    { stdio: ['ignore', 'ignore', 'pipe'] },
  );

  const exitPromise = new Promise((resolve) => {
    chrome.once('exit', () => resolve());
  });

  const wsEndpoint = await new Promise((resolve, reject) => {
    let stderrBuf = '';
    const timer = setTimeout(() => {
      reject(new Error(`Timed out waiting for Chrome DevTools URL. STDERR:\n${stderrBuf}`));
    }, 15000);

    chrome.stderr.on('data', (chunk) => {
      stderrBuf += chunk.toString('utf8');
      const m = /DevTools listening on (ws:\/\/[^\s]+)/.exec(stderrBuf);
      if (m) {
        clearTimeout(timer);
        resolve(m[1]);
      }
    });
    chrome.once('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });
    chrome.once('exit', (code) => {
      clearTimeout(timer);
      reject(new Error(`Chrome exited prematurely (${code}). STDERR:\n${stderrBuf}`));
    });
  });

  const baseHttpUrl = wsEndpoint.replace(/^ws:/, 'http:').replace(/\/devtools\/browser\/.*$/, '');
  const targetsResp = await fetch(`${baseHttpUrl}/json/list`);
  const targets = await targetsResp.json();
  const pageTarget = targets.find((t) => t.type === 'page') || targets[0];
  if (!pageTarget || !pageTarget.webSocketDebuggerUrl) {
    throw new Error(`No page target returned by Chrome DevTools: ${JSON.stringify(targets)}`);
  }

  const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', () => resolve());
    ws.addEventListener('error', (err) => reject(err));
  });

  let nextId = 1;
  const pending = new Map();
  const consoleErrors = [];
  const runtimeExceptions = [];
  const contextsByFrame = new Map();

  ws.addEventListener('message', (event) => {
    const msg = JSON.parse(String(event.data));
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) {
        reject(new Error(JSON.stringify(msg.error)));
      } else {
        resolve(msg.result);
      }
      return;
    }
    if (msg.method === 'Runtime.executionContextCreated' && msg.params?.context) {
      const ctx = msg.params.context;
      if (ctx.auxData?.isDefault && ctx.auxData?.frameId) {
        contextsByFrame.set(ctx.auxData.frameId, ctx.id);
      }
    } else if (msg.method === 'Runtime.executionContextDestroyed' && msg.params?.executionContextId) {
      for (const [frameId, ctxId] of contextsByFrame.entries()) {
        if (ctxId === msg.params.executionContextId) {
          contextsByFrame.delete(frameId);
        }
      }
    } else if (msg.method === 'Runtime.executionContextsCleared') {
      contextsByFrame.clear();
    } else if (msg.method === 'Runtime.consoleAPICalled' && msg.params?.type === 'error') {
      const text = (msg.params.args || []).map((a) => a.value ?? a.description ?? '').join(' ');
      consoleErrors.push(text);
    } else if (msg.method === 'Runtime.exceptionThrown') {
      const details = msg.params?.exceptionDetails;
      runtimeExceptions.push(details?.exception?.description || details?.text || 'Unknown exception');
    }
  });

  function send(method, params = {}) {
    const id = nextId++;
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async function evaluate(expression, contextId = undefined) {
    const params = {
      expression,
      awaitPromise: true,
      returnByValue: true,
    };
    if (contextId !== undefined) {
      params.contextId = contextId;
    }
    const res = await send('Runtime.evaluate', params);
    if (res.exceptionDetails) {
      throw new Error(`Page evaluation failed: ${JSON.stringify(res.exceptionDetails)}`);
    }
    return res.result?.value;
  }

  function collectFrames(treeNode, out = []) {
    if (treeNode && treeNode.frame) {
      out.push(treeNode.frame);
    }
    for (const child of treeNode?.childFrames || []) {
      collectFrames(child, out);
    }
    return out;
  }

  async function getQuotaIframeContextId(excludeContextId = null) {
    const { frameTree } = await send('Page.getFrameTree');
    const frames = collectFrames(frameTree);
    for (const frame of frames) {
      if (!String(frame.url || '').includes('quota_dashboard.html')) {
        continue;
      }
      const ctxId = contextsByFrame.get(frame.id);
      if (ctxId && ctxId !== excludeContextId) {
        try {
          const isQuota = await evaluate(
            `Boolean(document.getElementById('dashboardCard') && document.getElementById('scheduleModal'))`,
            ctxId,
          );
          if (isQuota) return ctxId;
        } catch (_) {}
      }
    }
    return null;
  }

  async function waitForQuotaIframeContext(readyExpr, excludeContextId = null, timeoutMs = 8000) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const ctxId = await getQuotaIframeContextId(excludeContextId);
      if (ctxId !== null) {
        try {
          if (await evaluate(readyExpr, ctxId)) return ctxId;
        } catch (_) {}
      }
      await new Promise((r) => setTimeout(r, 80));
    }
    return null;
  }

  async function clickAt(x, y) {
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await send('Input.dispatchMouseEvent', {
      type: 'mousePressed',
      x,
      y,
      button: 'left',
      clickCount: 1,
    });
    await send('Input.dispatchMouseEvent', {
      type: 'mouseReleased',
      x,
      y,
      button: 'left',
      clickCount: 1,
    });
  }

  async function pressEscape() {
    await send('Input.dispatchKeyEvent', {
      type: 'rawKeyDown',
      key: 'Escape',
      code: 'Escape',
      windowsVirtualKeyCode: 27,
      nativeVirtualKeyCode: 27,
    });
    await send('Input.dispatchKeyEvent', {
      type: 'keyUp',
      key: 'Escape',
      code: 'Escape',
      windowsVirtualKeyCode: 27,
      nativeVirtualKeyCode: 27,
    });
  }

  async function close() {
    try {
      ws.close();
    } catch (_) {}
    if (!chrome.killed && chrome.exitCode === null) {
      chrome.kill('SIGTERM');
    }
    const forceTimer = setTimeout(() => {
      if (chrome.exitCode === null) {
        try {
          chrome.kill('SIGKILL');
        } catch (_) {}
      }
    }, 3000);
    await exitPromise;
    clearTimeout(forceTimer);
    fs.rmSync(userDataDir, { recursive: true, force: true });
  }

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1280,
    height: 800,
    deviceScaleFactor: 1,
    mobile: false,
  });
  return {
    send,
    evaluate,
    waitForQuotaIframeContext,
    clickAt,
    pressEscape,
    close,
    consoleErrors,
    runtimeExceptions,
  };
}
"""


def _resolve_chrome_binary() -> str:
    """Resolve provisioned headless Google Chrome / Chromium binary or fail."""
    env_bin = os.environ.get("CHROME_BIN", "").strip()
    if env_bin and Path(env_bin).is_file():
        return env_bin
    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if mac_chrome.is_file():
        return str(mac_chrome)
    for candidate in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(candidate)
        if found:
            return found
    msg = "Provisioned headless Chrome binary not found (CHROME_BIN / macOS / PATH)"
    raise AssertionError(msg)


def _run_node_script(script_source: str, timeout: int = 60) -> dict[str, Any]:
    """Execute an ES module Node script and return its trailing JSON status line."""
    node_bin = shutil.which("node")
    assert node_bin, "Node.js v25+ is required for headless Chrome CDP assertions"
    proc = subprocess.run(
        [node_bin, "--input-type=module", "-e", script_source],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    assert proc.returncode == 0, (
        f"Node script failed ({proc.returncode}):\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, f"Node script produced empty stdout.\nSTDERR:\n{proc.stderr}"
    parsed = json.loads(lines[-1])
    assert isinstance(parsed, dict)
    return parsed


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    merged = {**os.environ, **ISOLATED_GIT_ENV}
    merged.pop("AGY_PROFILE", None)
    merged.pop("ANTIGRAVITY_PROFILE", None)
    if extra:
        merged.update(extra)
    return merged


def _run_cmd(
    cmd: list[str],
    *,
    cwd: Path,
    extra_env: dict[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=_env(extra_env),
        capture_output=True,
        text=True,
        check=False,
    )
    if check and proc.returncode != 0:
        msg = (
            f"Command {cmd} failed ({proc.returncode}) in {cwd}\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
        raise AssertionError(msg)
    return proc


def _git(cwd: Path, *args: str) -> str:
    return _run_cmd(["git", "-C", str(cwd), *args], cwd=cwd, check=True).stdout.strip()


def _find_dead_pid() -> int:
    """Return a high local PID guaranteed not to exist."""
    for candidate in range(950_000, 999_999):
        try:
            os.kill(candidate, 0)
        except ProcessLookupError:
            return candidate
        except PermissionError:
            continue
    msg = "Unable to allocate unused PID"
    raise AssertionError(msg)


def _import_script_module(name: str) -> ModuleType:
    return importlib.import_module(name)


def _seed_additional_epic(
    repo: Path,
    epic_dir: str,
    epic_slug: str,
    *,
    pic: str = "brother",
    task_id: str,
) -> None:
    """Create a lightweight sibling or roadmap epic inside .devtool/epic/."""
    ep_path = repo / ".devtool" / "epic" / epic_dir
    ep_path.mkdir(parents=True, exist_ok=True)
    (ep_path / f"{epic_dir}.en.md").write_text(
        f"# {epic_slug}\n\n- **Epic name**: `{epic_slug}`\n- **PIC**: `{pic}`\n- **Status**: unstarted\n",
        encoding="utf-8",
    )
    (ep_path / f"{task_id}.md").write_text(
        f'---\nid: "{task_id}"\nstatus: "todo"\nepic: "{epic_slug}"\npic: "{pic}"\n---\n\n# {task_id}\n',
        encoding="utf-8",
    )


def _seed_quality_provider(repo: Path) -> Path:
    """Register a lightweight Python capability under .agents/quality/ in repo."""
    cap_script = repo / "fast_check.py"
    cap_script.write_text(
        "import sys, time\nprint('CHECK_OK', flush=True)\ntime.sleep(0.22)\n",
        encoding="utf-8",
    )
    agents_dir = repo / ".agents" / "quality"
    agents_dir.mkdir(parents=True, exist_ok=True)
    registry = {
        "schema_version": 1,
        "providers": [
            {
                "id": "python-core",
                "skill": "d3nexus:python-quality-check",
                "required": True,
                "profiles": ["pr", "epic"],
            }
        ],
    }
    manifest = {
        "schema_version": 1,
        "capabilities": {
            "lint": ["ruff", "check", "tool.py"],
            "type_check": ["mypy", "tool.py"],
            "fast_check": [sys.executable, str(cap_script)],
            "architecture": [sys.executable, str(cap_script)],
        },
        "profiles": {
            "pr": ["fast_check"],
            "epic": ["fast_check", "architecture"],
        },
    }
    reg_file = agents_dir / "check_quality.json"
    reg_file.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    (agents_dir / "python-quality.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return reg_file


def _build_multi_worktree_workspace(tmp_path: Path) -> dict[str, Any]:
    """Initialize workspace root with ai-agent-tools multi-worktree repo and epics."""
    ws_root = tmp_path / "ws"
    repo = ws_root / "ai-agent-tools"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "RSDH Integration")
    _git(repo, "config", "user.email", "rsdh-int@example.com")

    build_ready_epic(repo)

    (repo / "tool.py").write_text(
        "from __future__ import annotations\n"
        "from pathlib import Path\n"
        "import sys\n\n"
        "def run() -> int:\n"
        "    mode = sys.argv[1] if len(sys.argv) > 1 else 'green'\n"
        "    if mode in ('red', 'red2'):\n"
        "        return 1\n"
        "    if mode == 'int':\n"
        "        out = Path('build/test-results/int.xml')\n"
        "        out.parent.mkdir(parents=True, exist_ok=True)\n"
        "        out.write_text(\n"
        "            '<testsuite tests=\"2\">'\n"
        '            \'<testcase classname="tests.Demo_Integration" name="DEMO-HP-01"/>\'\n'
        '            \'<testcase classname="tests.Demo_Integration" name="DEMO-HP-02"/>\'\n'
        "            '</testsuite>\\n',\n"
        "            encoding='utf-8',\n"
        "        )\n"
        "    return 0\n\n"
        "if __name__ == '__main__':\n"
        "    raise SystemExit(run())\n",
        encoding="utf-8",
    )

    # Declare a (new) file on task_1 so Stage 3 --revise ownership is exercised
    demo_dir = repo / ".devtool" / "epic" / "demo_epic"
    for t1_path in (
        demo_dir / "task_1.md",
        repo / ".devtool" / "features" / "task_1.md",
    ):
        t1_path.write_text(
            t1_path.read_text(encoding="utf-8").replace(
                "- `tool.py`", "- `tool.py`\n- `src/delivered.py` (new)", 1
            ),
            encoding="utf-8",
        )

    bdd_file = demo_dir / "bdd_scenarios.en.md"
    review_file = demo_dir / "principal_review.md"
    review_file.write_text(
        "# Principal Review\n\n- **Verdict**: PASS\n", encoding="utf-8"
    )

    _seed_additional_epic(
        repo, "alpha_road", "alpha-road", pic="mommy", task_id="task_a1"
    )
    _seed_additional_epic(
        repo, "beta_road", "beta-road", pic="danhdue", task_id="task_b1"
    )
    _seed_additional_epic(
        repo, "sibling_epic", "sibling-epic", pic="mommy", task_id="task_sib_1"
    )

    reg_file = _seed_quality_provider(repo)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Initial multi-epic workspace")

    # Apply distinct same-day UTC timestamps on alpha_road (01:00) vs beta_road (08:00)
    today_utc = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    t_alpha = today_utc.replace(hour=1).timestamp()
    t_beta = today_utc.replace(hour=8).timestamp()
    for ep_name, ts in (("alpha_road", t_alpha), ("beta_road", t_beta)):
        ep_dir = repo / ".devtool" / "epic" / ep_name
        for child in ep_dir.iterdir():
            os.utime(child, (ts, ts))
        os.utime(ep_dir, (ts, ts))

    return {
        "ws_root": ws_root,
        "repo": repo,
        "reg_file": reg_file,
        "bdd_bytes": bdd_file.read_bytes(),
        "review_bytes": review_file.read_bytes(),
        "today_utc": today_utc,
    }


@contextlib.contextmanager
def _start_live_servers(
    ws_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Any:
    """Launch bound 127.0.0.1 static Quota server and live TasksServer."""
    quota_html_bytes = QUOTA_DASHBOARD_HTML.read_bytes()

    class _QuotaHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def do_GET(self) -> None:
            req_path = self.path.split("?", 1)[0]
            if req_path in ("/", "/index.html", "/quota_dashboard.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(quota_html_bytes)))
                self.end_headers()
                self.wfile.write(quota_html_bytes)
                return
            if req_path == "/api/status":
                payload = json.dumps(
                    {
                        "success": True,
                        "profiles": {},
                        "can_auto_refresh": False,
                        "elapsed_seconds": 60,
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            self.send_response(204)
            self.end_headers()

    quota_port = tasks_server.find_available_port(19620)
    quota_http = http.server.ThreadingHTTPServer(
        ("127.0.0.1", quota_port), _QuotaHandler
    )
    threading.Thread(target=quota_http.serve_forever, daemon=True).start()

    monkeypatch.setattr(
        tasks_server,
        "launch_quota_server",
        lambda workspace_root, port=8765: {
            "status": "ok",
            "action": "mock_ephemeral",
            "url": f"http://127.0.0.1:{quota_port}/quota_dashboard.html",
        },
    )

    tasks_port = tasks_server.find_available_port(19720)
    srv = tasks_server.TasksServer(
        host="127.0.0.1",
        port=tasks_port,
        workspace_root=ws_root,
        pid_file=tmp_path / "tasks_server.pid",
    )
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.1)

    try:
        yield {
            "tasks_url": f"http://127.0.0.1:{srv.server_port}",
            "quota_url": f"http://127.0.0.1:{quota_port}/quota_dashboard.html",
        }
    finally:
        srv.shutdown()
        srv.server_close()
        quota_http.shutdown()
        quota_http.server_close()


def _http_get_json(url: str) -> tuple[int, dict[str, Any]]:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def _http_post_json(url: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def _verify_orchestration_and_quality_phases(
    ws: dict[str, Any], tmp_path: Path
) -> dict[str, Any]:
    """Run Stage 2->3 packaging, envelope sync, estimator, quality runner, and pool cleanup."""
    repo: Path = ws["repo"]
    reg_file: Path = ws["reg_file"]
    prof_home = tmp_path / "antigravity_homes" / "brother"
    prof_home.mkdir(parents=True)
    prof_env = {
        "HOME": str(prof_home),
        "ANTIGRAVITY_PROFILE": "brother",
        "USER": "nobody",
    }

    detect_proc = _run_cmd(
        [sys.executable, str(RESUME_SCRIPT), "--detect-profile"],
        cwd=repo,
        extra_env=prof_env,
        check=True,
    )
    assert detect_proc.stdout.strip() == "brother"

    for gate_num, approved in (("1", "Spec approved"), ("2", "HLD approved")):
        _run_cmd(
            [
                sys.executable,
                str(RESUME_SCRIPT),
                "--gate",
                gate_num,
                "--epic",
                "demo-epic",
                "--approved",
                approved,
            ],
            cwd=repo,
            extra_env=prof_env,
            check=True,
        )

    pkg_proc = _run_cmd(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic"],
        cwd=repo,
        extra_env=prof_env,
    )
    assert pkg_proc.returncode == 0, pkg_proc.stdout + pkg_proc.stderr
    handoff_file = repo / ".devtool" / "epic" / "demo_epic" / "handoff.md"
    handoff_text = handoff_file.read_text(encoding="utf-8")
    assert "<profile_account_id>" not in handoff_text
    assert re.search(r"PIC / Assigned Profile\*\*:\s*`?@?brother`?", handoff_text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Package demo_epic handoff")

    # Create active epic worktree + sync window title
    wt = repo / ".worktrees" / "demo_epic"
    _git(repo, "worktree", "add", "-q", str(wt), "-b", "epic/demo-epic", "main")
    resume_mod = _import_script_module("resume_context")
    resume_mod.sync_window_title(wt, epic_slug="demo-epic", profile_override="brother")
    wt_vscode = wt / ".vscode" / "settings.json"
    assert wt_vscode.is_file()
    assert "[@brother]" in wt_vscode.read_text(encoding="utf-8")
    _git(wt, "add", ".vscode/settings.json")
    _git(wt, "commit", "-q", "-m", "Record initial worktree window title")

    # Record Choice A pending decisions for both demo-epic and sibling-epic
    for epic_slug, reason in (
        ("demo-epic", "Confirm Gate 3 wave execution"),
        ("sibling-epic", "Sibling approval still pending"),
    ):
        _run_cmd(
            [
                sys.executable,
                str(RESUME_SCRIPT),
                "--pending-decision",
                reason,
                "--decision-kind",
                "gate_3_choice",
                "--epic",
                epic_slug,
            ],
            cwd=wt,
            extra_env=prof_env,
            check=True,
        )

    # Approve Gate 3 inside worktree and deliver task_1 + task_2 via sync_task_status
    _run_cmd(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--gate",
            "3",
            "--epic",
            "demo-epic",
            "--approved",
            "Stage 3 active",
        ],
        cwd=wt,
        extra_env=prof_env,
        check=True,
    )

    # Advance task_1 and task_2 through genuine TDD red -> code -> verify -> done
    # Step 1: task_1 in-progress (clears demo-epic pending_decision only)
    _run_cmd(
        [sys.executable, str(SYNC_TASK_SCRIPT), "task", "task_1", "in-progress"],
        cwd=wt,
        check=True,
    )

    # Verify sibling-epic decision stays isolated when demo-epic advances
    env_mod = _import_script_module("_state_envelope")
    pdec_mid = env_mod.read_json_safe(
        repo / ".devtool" / "state" / "pending_decision.json", {}
    )
    assert "demo-epic" not in pdec_mid.get("decisions", {})
    assert "sibling-epic" in pdec_mid.get("decisions", {})

    _run_cmd(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--clear-decision",
            "--epic",
            "sibling-epic",
        ],
        cwd=wt,
        extra_env=prof_env,
        check=True,
    )

    _run_cmd(
        [
            sys.executable,
            str(RUN_TASK_CHECKS_SCRIPT),
            "red",
            ".devtool/epic/demo_epic/task_1.md",
        ],
        cwd=wt,
        check=True,
    )
    (wt / "src").mkdir(parents=True, exist_ok=True)
    (wt / "src" / "delivered.py").write_text("READY = True\n", encoding="utf-8")
    _run_cmd(
        [
            sys.executable,
            str(RUN_TASK_CHECKS_SCRIPT),
            "verify",
            ".devtool/epic/demo_epic/task_1.md",
        ],
        cwd=wt,
        check=True,
    )
    _run_cmd(
        [sys.executable, str(SYNC_TASK_SCRIPT), "task", "task_1", "done"],
        cwd=wt,
        check=True,
    )
    _git(wt, "add", "-A")
    _git(wt, "commit", "-q", "-m", "Deliver task_1")

    # Step 2: task_2 in-progress -> red -> edit tool.py -> verify -> done
    _run_cmd(
        [sys.executable, str(SYNC_TASK_SCRIPT), "task", "task_2", "in-progress"],
        cwd=wt,
        check=True,
    )
    _run_cmd(
        [
            sys.executable,
            str(RUN_TASK_CHECKS_SCRIPT),
            "red",
            ".devtool/epic/demo_epic/task_2.md",
        ],
        cwd=wt,
        check=True,
    )
    (wt / "tool.py").write_text(
        (wt / "tool.py").read_text(encoding="utf-8") + "# task_2 delivered\n",
        encoding="utf-8",
    )
    _run_cmd(
        [
            sys.executable,
            str(RUN_TASK_CHECKS_SCRIPT),
            "verify",
            ".devtool/epic/demo_epic/task_2.md",
        ],
        cwd=wt,
        check=True,
    )
    _run_cmd(
        [sys.executable, str(SYNC_TASK_SCRIPT), "task", "task_2", "done"],
        cwd=wt,
        check=True,
    )

    # Dual-root heartbeat + Two-Tier memory synchronized identically
    root_hb = env_mod.read_json_safe(
        repo / ".devtool" / "state" / "demo-epic.heartbeat.json", {}
    )
    wt_hb = env_mod.read_json_safe(
        wt / ".devtool" / "state" / "demo-epic.heartbeat.json", {}
    )
    assert root_hb == wt_hb
    assert root_hb.get("generation", 0) >= 4
    assert (repo / ".devtool" / "state" / "demo-epic.md").is_file()
    assert (repo / ".devtool" / "assistant_state.md").is_file()

    # Stage 3 package_epic --revise must accept task_1's existing (new) deliverable
    _git(wt, "add", "-A")
    _git(wt, "commit", "-q", "-m", "Deliver task_2")
    rev_proc = _run_cmd(
        [
            sys.executable,
            str(PACKAGE_SCRIPT),
            "--revise",
            "--reason",
            "Stage 3 wave update",
            "demo_epic",
        ],
        cwd=wt,
        extra_env=prof_env,
    )
    assert rev_proc.returncode == 0, rev_proc.stdout + rev_proc.stderr
    assert "<profile_account_id>" not in (
        wt / ".devtool" / "epic" / "demo_epic" / "handoff.md"
    ).read_text(encoding="utf-8")

    # Worker pool init -> sync working slot -> resume --wave -> safe cleanup
    _run_cmd(
        [sys.executable, str(POOL_SCRIPT), "init", "demo_epic", "--pool-size", "1"],
        cwd=wt,
        check=True,
    )
    _run_cmd(
        [
            sys.executable,
            str(POOL_SCRIPT),
            "sync",
            "--epic-dir",
            "demo_epic",
            "--epic-slug",
            "demo-epic",
            "--slot",
            "1",
            "--task",
            "task_2",
            "--wave",
            "1",
        ],
        cwd=wt,
        check=True,
    )
    _run_cmd(
        [sys.executable, str(RESUME_SCRIPT), "--wave", "1", "--epic", "demo-epic"],
        cwd=wt,
        check=True,
    )
    working_hb = env_mod.read_json_safe(
        repo / ".devtool" / "state" / "demo-epic.heartbeat.json", {}
    )
    assert working_hb.get("active_wave") == 1
    assert working_hb.get("slots", {}).get("slot-1", {}).get("status") == "working"

    cleanup_proc = _run_cmd(
        [
            sys.executable,
            str(POOL_SCRIPT),
            "cleanup",
            "--epic-dir",
            "demo_epic",
            "--epic-slug",
            "demo-epic",
        ],
        cwd=wt,
    )
    assert cleanup_proc.returncode == 0, cleanup_proc.stdout + cleanup_proc.stderr
    cleaned_hb = env_mod.read_json_safe(
        repo / ".devtool" / "state" / "demo-epic.heartbeat.json", {}
    )
    assert cleaned_hb.get("slots") == {}

    # Estimate heartbeat + run verify_polyglot_registry with fast interval
    est_proc = _run_cmd(
        [
            sys.executable,
            str(ESTIMATE_SCRIPT),
            "--epic-dir",
            "demo_epic",
            "--quality-profile",
            "epic",
            "--has-e2e",
            "--json",
        ],
        cwd=repo,
        check=True,
    )
    est_data = json.loads(est_proc.stdout)
    assert est_data["tier"] == "heavy"
    assert est_data["recommended_interval_sec"] == 300

    qc_proc = _run_cmd(
        [
            sys.executable,
            str(VERIFY_QC_SCRIPT),
            str(reg_file),
            "--profile",
            "epic",
            "--execute",
            "--compact",
            "--heartbeat-interval",
            "0.05",
            "--epic",
            "demo-epic",
        ],
        cwd=repo,
    )
    assert qc_proc.returncode == 0, qc_proc.stdout + qc_proc.stderr
    assert "[quality_check]" in qc_proc.stderr
    qa_after = env_mod.read_json_safe(
        repo / ".devtool" / "state" / "quality_active.json", {}
    )
    assert qa_after.get("status") == "passed"

    # Inject a live concurrent run AND a stale dead-PID expired entry for harvester validation
    env_mod.update_quality_run(
        repo,
        "live-concurrent-run",
        epic_slug="demo-epic",
        profile="epic",
        status="running",
        provider="python-qa",
        capability="lint",
        step_index=1,
        step_total=3,
        pid=os.getpid(),
        ttl_sec=300,
    )
    expired_ts = (datetime.now(timezone.utc) - timedelta(seconds=600)).isoformat(
        timespec="seconds"
    )
    env_mod.update_quality_run(
        repo,
        "dead-stale-run",
        epic_slug="demo-epic",
        profile="epic",
        status="running",
        provider="python-qa",
        capability="test",
        step_index=2,
        step_total=3,
        pid=_find_dead_pid(),
        ttl_sec=30,
        started_at=expired_ts,
        updated_at=expired_ts,
    )
    return {"wt": wt, "env_mod": env_mod, "prof_env": prof_env}


def _run_chrome_cdp_e2e(
    urls: dict[str, str],
    repo: Path,
    wt: Path,
    env_mod: ModuleType,
    today_utc: datetime,
    tmp_path: Path,
) -> None:
    """Exercise tasks_dashboard.html + embedded quota_dashboard.html in real Chrome CDP."""
    chrome_bin = _resolve_chrome_binary()
    cdp_helper_path = tmp_path / "cdp_helper.mjs"
    cdp_helper_path.write_text(_NODE_CDP_HELPER, encoding="utf-8")

    # Control server to mutate wave/quality state and bump beta_road mtime mid-session
    class _CtrlHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def do_POST(self) -> None:
            if self.path == "/advance-wave":
                env_mod.update_epic_heartbeat(
                    wt,
                    "demo-epic",
                    stage="Stage 3 Phase 4 (Verification & Review)",
                    active_wave=2,
                    last_event="wave 2 verification active",
                )
                env_mod.update_quality_run(
                    repo,
                    "live-concurrent-run",
                    epic_slug="demo-epic",
                    profile="epic",
                    status="running",
                    provider="python-qa",
                    capability="mypy",
                    step_index=2,
                    step_total=3,
                    pid=os.getpid(),
                    ttl_sec=300,
                )
                self.send_response(200)
                self.end_headers()
                return
            if self.path == "/bump-beta":
                t_beta_newer = today_utc.replace(hour=16, minute=15).timestamp()
                beta_dir = repo / ".devtool" / "epic" / "beta_road"
                (beta_dir / "task_b2.md").write_text(
                    '---\nid: "task_b2"\nstatus: "todo"\nepic: "beta-road"\n---\n# Task B2\n',
                    encoding="utf-8",
                )
                for child in beta_dir.iterdir():
                    os.utime(child, (t_beta_newer, t_beta_newer))
                os.utime(beta_dir, (t_beta_newer, t_beta_newer))
                self.send_response(200)
                self.end_headers()
                return
            self.send_response(404)
            self.end_headers()

    ctrl_port = tasks_server.find_available_port(19920)
    ctrl_srv = http.server.ThreadingHTTPServer(("127.0.0.1", ctrl_port), _CtrlHandler)
    threading.Thread(target=ctrl_srv.serve_forever, daemon=True).start()

    cdp_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(cdp_helper_path))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Page.navigate', {{ url: {json.dumps(urls["tasks_url"] + "/")} }});
  let ready = false;
  for (let i = 0; i < 40; i++) {{
    ready = await cdp.evaluate(`Boolean(document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools .epic-execution-item'))`);
    if (ready) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.ok(ready, 'Dashboard Section II must mount from live TasksServer');

  await cdp.evaluate(`window.__rsdhNoReload = 'ok'`);

  // 1. Verify weighted 83% running-QA progress + 100% task completion in Section I and Section II (never 99% or 100% lifecycle)
  const sec1Text = await cdp.evaluate(`document.getElementById('kanban-dashboard-wrapper-ai-agent-tools').innerText`);
  const sec2Text = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  assert.ok(sec1Text.includes('83%'), `Section I must render 83% weighted running-QA progress, got: ${{sec1Text}}`);
  assert.ok(sec1Text.includes('2/2 Tasks (100%)'), `Section I must render 100% task completion, got: ${{sec1Text}}`);
  assert.ok(!sec1Text.includes('99%'), 'Section I must not render 99%');
  assert.ok(sec2Text.includes('83%'), `Section II must render 83% weighted running-QA progress, got: ${{sec2Text}}`);
  assert.ok(sec2Text.includes('100%'), `Section II must render 100% task completion, got: ${{sec2Text}}`);
  assert.ok(sec2Text.includes('live-concurrent-run') || sec2Text.includes('lint'), `Section II must show running quality step`);

  // 2. Live Section II tier2Sig refresh on disk change without page reload
  await fetch({json.dumps(f"http://127.0.0.1:{ctrl_port}/advance-wave")}, {{ method: 'POST' }});
  await cdp.evaluate(`pollDashboard()`);
  const sec2After = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  assert.equal(await cdp.evaluate(`window.__rsdhNoReload`), 'ok');
  assert.ok(sec2After.includes('mypy') || sec2After.includes('2/3') || sec2After.includes('wave 2'),
    `Section II must refresh incrementally on poll, got: ${{sec2After}}`);

  // 3. Roadmap same-day order stability + native <select> focus retention during poll
  const initialKeys = await cdp.evaluate(
    `Array.from(document.querySelectorAll('#roadmap-tbody-ai-agent-tools .roadmap-epic-row')).map(r => r.getAttribute('data-row-key'))`
  );
  const alphaIdx = initialKeys.indexOf('ai-agent-tools:alpha_road');
  const betaIdx = initialKeys.indexOf('ai-agent-tools:beta_road');
  assert.ok(alphaIdx !== -1 && betaIdx !== -1 && alphaIdx < betaIdx,
    `alpha_road must precede beta_road despite older same-day mtime: ${{JSON.stringify(initialKeys)}}`);

  const focused = await cdp.evaluate(`(() => {{
    const sel = document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap[data-row-key="ai-agent-tools:alpha_road"]');
    if (!sel) return false;
    sel.focus();
    window.__heldRoadmapSelect = sel;
    return document.activeElement === sel;
  }})()`);
  assert.equal(focused, true, 'Roadmap select must hold activeElement focus');

  await fetch({json.dumps(f"http://127.0.0.1:{ctrl_port}/bump-beta")}, {{ method: 'POST' }});
  await cdp.evaluate(`pollDashboard()`);
  const focusCheck = await cdp.evaluate(`(() => {{
    const sel = document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap[data-row-key="ai-agent-tools:alpha_road"]');
    return {{ sameNode: sel === window.__heldRoadmapSelect, isActive: document.activeElement === window.__heldRoadmapSelect }};
  }})()`);
  assert.equal(focusCheck.sameNode, true, 'Focused select node must survive pollDashboard');
  assert.equal(focusCheck.isActive, true, 'document.activeElement must remain focused');

  await cdp.evaluate(`(() => {{
    const sel = window.__heldRoadmapSelect;
    sel.value = 'brother';
    sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
    sel.blur();
  }})()`);

  // Wait for queued poll flush after blur (beta_road task count 2)
  let betaTasksCell = null;
  for (let i = 0; i < 30; i++) {{
    betaTasksCell = await cdp.evaluate(
      `document.querySelectorAll('#roadmap-tbody-ai-agent-tools tr[data-row-key="ai-agent-tools:beta_road"] td')[3]?.textContent?.trim()`
    );
    if (betaTasksCell === '2') break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.equal(betaTasksCell, '2', 'Queued Roadmap update must flush after select blur');

  // 4. Open #modal-quota -> verify real ?embedded=1 quota_dashboard.html flattening + Single Modal Stack + Escape + postMessage reset
  await cdp.evaluate(`openQuotaModal()`);
  const iframeCtx = await cdp.waitForQuotaIframeContext(
    `typeof getActiveInnerModal === 'function' && typeof openScheduleModal === 'function'`,
  );
  assert.ok(iframeCtx !== null, 'Quota iframe context must initialize');
  const iframeSrc = await cdp.evaluate(`document.getElementById('quota-iframe').getAttribute('src')`);
  assert.ok(iframeSrc.includes('embedded=1'), `Expected ?embedded=1 on iframe src, got: ${{iframeSrc}}`);

  const cardStyle = await cdp.evaluate(`(() => {{
    const cs = getComputedStyle(document.getElementById('dashboardCard'));
    const bs = getComputedStyle(document.body);
    return {{
      borderTopWidth: cs.borderTopWidth,
      boxShadow: cs.boxShadow,
      borderRadius: cs.borderRadius,
      paddingTop: cs.paddingTop,
      bodyPaddingTop: bs.paddingTop,
    }};
  }})()`, iframeCtx);
  assert.equal(cardStyle.borderTopWidth, '0px');
  assert.equal(cardStyle.boxShadow, 'none');
  assert.equal(cardStyle.borderRadius, '0px');
  assert.equal(cardStyle.paddingTop, '10px');
  assert.equal(cardStyle.bodyPaddingTop, '0px');

  const getOpenIdsExpr = `['scheduleModal', 'loginModal', 'profileInfoModal', 'appealDetailModal'].filter(id => !document.getElementById(id).classList.contains('hidden'))`;
  await cdp.evaluate(`openScheduleModal('brother')`, iframeCtx);
  assert.deepEqual(await cdp.evaluate(getOpenIdsExpr, iframeCtx), ['scheduleModal']);

  await cdp.evaluate(`openLoginModal('brother')`, iframeCtx);
  assert.deepEqual(await cdp.evaluate(getOpenIdsExpr, iframeCtx), ['loginModal']);

  // Focus inside loginModal and press Escape -> closes ONLY #loginModal, keeping #modal-quota open
  const iframeRect = await cdp.evaluate(`(() => {{
    const r = document.getElementById('quota-iframe').getBoundingClientRect();
    return {{ left: r.left, top: r.top }};
  }})()`);
  const cardPt = await cdp.evaluate(`(() => {{
    const r = document.getElementById('loginModal').firstElementChild.getBoundingClientRect();
    return {{ x: r.left + r.width / 2, y: r.top + 20 }};
  }})()`, iframeCtx);
  await cdp.clickAt(iframeRect.left + cardPt.x, iframeRect.top + cardPt.y);
  await cdp.pressEscape();
  await new Promise((r) => setTimeout(r, 80));

  assert.deepEqual(await cdp.evaluate(getOpenIdsExpr, iframeCtx), []);
  assert.equal(await cdp.evaluate(`getComputedStyle(document.getElementById('modal-quota')).display`), 'flex');

  // Reopen scheduleModal, then close parent #modal-quota -> postMessage reset closes inner sub-modal
  await cdp.evaluate(`openScheduleModal('brother')`, iframeCtx);
  await cdp.evaluate(`closeLiveModal('modal-quota')`);
  let cleared = [];
  for (let i = 0; i < 30; i++) {{
    cleared = await cdp.evaluate(getOpenIdsExpr, iframeCtx);
    if (cleared.length === 0) break;
    await new Promise((r) => setTimeout(r, 50));
  }}
  assert.deepEqual(cleared, [], 'Closing #modal-quota must post reset_quota_submodals to iframe');

  assert.deepEqual(cdp.consoleErrors, [], `Unexpected browser console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected browser exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok', betaTasksCell }}));
}} finally {{
  await cdp.close();
}}
"""
    try:
        res = _run_node_script(cdp_script, timeout=60)
        assert res["status"] == "ok"
    finally:
        ctrl_srv.shutdown()
        ctrl_srv.server_close()


def test_rsdh_hp_09_cross_layer_orchestration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[RSDH-HP-09] [Tier C - Integration] End-to-end orchestration, envelope sync, 96% dashboard, PIC sync, and Chrome CDP modal stack pass together."""
    ws = _build_multi_worktree_workspace(tmp_path)
    repo: Path = ws["repo"]
    ws_root: Path = ws["ws_root"]

    phase_info = _verify_orchestration_and_quality_phases(ws, tmp_path)
    wt: Path = phase_info["wt"]
    env_mod: ModuleType = phase_info["env_mod"]

    with _start_live_servers(ws_root, tmp_path, monkeypatch) as urls:
        # 1. Verify /api/tasks exposes 96% pre-finish progress, cleared decision, live quality_runs, and stale expiry
        status_code, tasks_payload = _http_get_json(f"{urls['tasks_url']}/api/tasks")
        assert status_code == 200
        repo_entry = next(
            r for r in tasks_payload["repos"] if r["name"] == "ai-agent-tools"
        )
        assert repo_entry["active_epic"] == "demo_epic"
        assert repo_entry["task_progress"]["percentage"] == 96.0
        assert repo_entry["is_human_action_required"] is False
        assert repo_entry["pending_decision"] is None
        run_ids = [r["run_id"] for r in repo_entry.get("quality_runs", [])]
        assert "live-concurrent-run" in run_ids
        assert "dead-stale-run" not in run_ids

        # 2. Reassign PIC across root + worktree via live HTTP POST /api/epic/pic
        post_code, pic_resp = _http_post_json(
            f"{urls['tasks_url']}/api/epic/pic",
            {"repo": "ai-agent-tools", "epic": "demo_epic", "pic": "tess"},
        )
        assert post_code == 200
        assert pic_resp["status"] == "ok"

        for checkout in (repo, wt):
            ep_dir = checkout / ".devtool" / "epic" / "demo_epic"
            assert "`tess`" in (ep_dir / "demo_epic.en.md").read_text(encoding="utf-8")
            assert "`tess`" in (ep_dir / "handoff.md").read_text(encoding="utf-8")
            assert 'pic: "tess"' in (ep_dir / "task_1.md").read_text(encoding="utf-8")
        assert "[@tess]" in (wt / ".vscode" / "settings.json").read_text(
            encoding="utf-8"
        )
        assert (
            repo / ".devtool" / "epic" / "demo_epic" / "bdd_scenarios.en.md"
        ).read_bytes() == ws["bdd_bytes"]
        assert (
            repo / ".devtool" / "epic" / "demo_epic" / "principal_review.md"
        ).read_bytes() == ws["review_bytes"]
        assert (
            wt / ".devtool" / "epic" / "demo_epic" / "bdd_scenarios.en.md"
        ).read_bytes() == ws["bdd_bytes"]
        assert (
            wt / ".devtool" / "epic" / "demo_epic" / "principal_review.md"
        ).read_bytes() == ws["review_bytes"]

        # 3. Real provisioned headless Chrome CDP across parent tasks_dashboard + embedded quota_dashboard iframe
        _run_chrome_cdp_e2e(
            urls,
            repo,
            wt,
            env_mod,
            ws["today_utc"],
            tmp_path,
        )


def _extract_verify_suites(verify_text: str) -> list[str]:
    """Parse SUITES literal tuples inside scripts/verify.sh without running verify.sh."""
    m = re.search(
        r"^(SUITES\s*=\s*\[.*?^\])", verify_text, flags=re.MULTILINE | re.DOTALL
    )
    assert m, "SUITES list not found inside scripts/verify.sh"
    tree = ast.parse(m.group(1))
    assign = tree.body[0]
    assert isinstance(assign, ast.Assign)
    raw_list = ast.literal_eval(assign.value)
    assert isinstance(raw_list, list)
    return [str(entry[2]) for entry in raw_list]


def test_rsdh_fr_06_verify_and_byte_budget_invariants(tmp_path: Path) -> None:
    """[RSDH-FR-06] [Tier C - Integration] Registered verification suites guard byte budgets, idle false positives, and snapshot isolation continuously."""
    # 1. Byte budgets for rules/CRITICAL_RULES.md and skills/dev-designer/SKILL.md
    critical_bytes = (REPO_ROOT / "rules" / "CRITICAL_RULES.md").read_bytes()
    assert len(critical_bytes) <= 8192, (
        f"rules/CRITICAL_RULES.md exceeded 8192B budget: {len(critical_bytes)}B"
    )
    designer_bytes = (REPO_ROOT / "skills" / "dev-designer" / "SKILL.md").read_bytes()
    assert len(designer_bytes) <= 22528, (
        f"skills/dev-designer/SKILL.md exceeded 22528B budget: {len(designer_bytes)}B"
    )

    # 2. Idle repository check: no alphabetical fallback onto unstarted epic dirs (e.g. choosing_a_lifecycle)
    check_tasks_text = (CHECK_TASKS_SCRIPTS / "check_tasks.py").read_text(
        encoding="utf-8"
    )
    assert "Strategy 7" not in check_tasks_text
    assert "Approve Gate 1 (Design Spec)" not in check_tasks_text

    idle_repo = tmp_path / "idle-repo"
    idle_repo.mkdir()
    _git(idle_repo, "init", "-q", "-b", "main")
    _git(idle_repo, "config", "user.name", "RSDH Idle")
    _git(idle_repo, "config", "user.email", "idle@example.com")
    (idle_repo / "README.md").write_text("# Idle\n", encoding="utf-8")
    unstarted = idle_repo / ".devtool" / "epic" / "choosing_a_lifecycle"
    unstarted.mkdir(parents=True)
    (unstarted / "choosing_a_lifecycle.en.md").write_text(
        "# Choosing\n\n- **Status**: unstarted\n", encoding="utf-8"
    )
    _git(idle_repo, "add", "-A")
    _git(idle_repo, "commit", "-q", "-m", "Idle repo with unstarted epic")

    assert check_tasks.resolve_active_epic(idle_repo) is None
    idle_decision = check_tasks.derive_lifecycle_state(idle_repo, None)
    assert idle_decision.stage_name == check_tasks.LifecycleStage.IDLE.value
    assert idle_decision.is_human_action_required is False

    # 3. Handoff template & package_epic creator profile stamping leave zero <profile_account_id>
    tpl_text = (
        REPO_ROOT / "skills" / "dev-lifecycle" / "references" / "handoff-template.md"
    ).read_text(encoding="utf-8")
    assert "compute_execution_order.py" in tpl_text
    assert "--parallel" in tpl_text
    assert "manage_worker_pool.py" in tpl_text
    assert "Sequentially execute each Kanban task" not in tpl_text

    pkg_repo = tmp_path / "pkg-repo"
    pkg_repo.mkdir()
    _git(pkg_repo, "init", "-q", "-b", "main")
    _git(pkg_repo, "config", "user.name", "RSDH Pkg")
    _git(pkg_repo, "config", "user.email", "pkg@example.com")
    build_ready_epic(pkg_repo)
    _git(pkg_repo, "add", "-A")
    _git(pkg_repo, "commit", "-q", "-m", "Ready epic")
    prof_env = {"ANTIGRAVITY_PROFILE": "brother", "USER": "nobody"}
    for gate_num, msg in (("1", "G1"), ("2", "G2")):
        _run_cmd(
            [
                sys.executable,
                str(RESUME_SCRIPT),
                "--gate",
                gate_num,
                "--epic",
                "demo-epic",
                "--approved",
                msg,
            ],
            cwd=pkg_repo,
            extra_env=prof_env,
            check=True,
        )
    pkg_res = _run_cmd(
        [sys.executable, str(PACKAGE_SCRIPT), "demo_epic"],
        cwd=pkg_repo,
        extra_env=prof_env,
    )
    assert pkg_res.returncode == 0, pkg_res.stdout + pkg_res.stderr
    rendered_handoff = (
        pkg_repo / ".devtool" / "epic" / "demo_epic" / "handoff.md"
    ).read_text(encoding="utf-8")
    assert "<profile_account_id>" not in rendered_handoff
    assert "`brother`" in rendered_handoff

    # 4. scripts/verify.sh SUITES registration (non-recursive: never spawns verify.sh here)
    verify_text = (REPO_ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")
    registered_suites = _extract_verify_suites(verify_text)
    for suite_rel in EXPECTED_EPIC_SUITES:
        assert suite_rel in registered_suites, (
            f"Missing '{suite_rel}' in scripts/verify.sh SUITES"
        )
        assert (REPO_ROOT / suite_rel).is_file(), (
            f"Registered suite not found: {suite_rel}"
        )

    # 5. .agents/quality/python-quality.json standing coverage of new scripts/ modules
    pq = json.loads(
        (REPO_ROOT / ".agents" / "quality" / "python-quality.json").read_text(
            encoding="utf-8"
        )
    )
    assert pq.get("schema_version") == 1
    caps = pq.get("capabilities", {})
    for cap_name in ("format", "lint", "type_check"):
        cmd_tokens = caps.get(cap_name, [])
        for script_rel in EXPECTED_NEW_SCRIPTS:
            assert script_rel in cmd_tokens, (
                f"Missing '{script_rel}' in python-quality.json capabilities.{cap_name}"
            )
    assert "scripts/verify.sh" in caps.get("architecture", [])


class TestRuntimeSyncAndDashboardHardening_Integration:
    """[Tier C - Integration] Integration runner provenance suite for Task 07 scenarios."""

    def test_rsdh_hp_09_integration(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[RSDH-HP-09] Integration check for cross-layer orchestration and Chrome CDP."""
        test_rsdh_hp_09_cross_layer_orchestration(tmp_path, monkeypatch)

    def test_rsdh_fr_06_integration(self, tmp_path: Path) -> None:
        """[RSDH-FR-06] Integration check for verify registration and byte budgets."""
        test_rsdh_fr_06_verify_and_byte_budget_invariants(tmp_path)
