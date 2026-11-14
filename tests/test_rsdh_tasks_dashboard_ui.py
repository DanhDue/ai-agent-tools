"""UI & Chrome CDP integration tests for tasks_dashboard.html hardening.

Covers BDD Scenarios:
- RSDH-HP-07: Tasks dashboard enforces 96% pre-finish ceiling and refreshes Section II live on state changes
- RSDH-EC-06: Roadmap eliminates sub-day mtime sorting and preserves native select focus in Chrome CDP
- RSDH-ST-05: Progress calculation enforces 75% mid-epic, 95% in-progress cap, 96% pre-finish cap, and 100% finished state
- RSDH-AR-02: Live polling applies Tier 2 updates immediately without clobbering focused controls or emitting console errors
"""

from __future__ import annotations

from datetime import datetime, timezone
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


def _resolve_chrome_binary() -> str:
    """Resolve provisioned Google Chrome or Chromium binary for headless CDP tests."""
    env_bin = os.environ.get("CHROME_BIN", "").strip()
    if env_bin and Path(env_bin).is_file():
        return env_bin

    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if mac_chrome.is_file():
        return str(mac_chrome)

    for candidate in ("google-chrome", "chromium", "chromium-browser"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    msg = (
        "Headless Chrome binary not found (checked CHROME_BIN, macOS Chrome, and PATH)"
    )
    pytest.fail(msg)
    raise RuntimeError(msg)


def _run_node_script(script_source: str, timeout: int = 30) -> dict[str, Any]:
    """Execute a Node.js (v25+) verification script and parse its JSON stdout."""
    node_bin = shutil.which("node")
    assert node_bin is not None, "Node.js binary must be installed"

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".mjs",
        encoding="utf-8",
        delete=False,
    ) as tmp_file:
        tmp_file.write(script_source)
        script_path = Path(tmp_file.name)

    try:
        proc = subprocess.run(
            [node_bin, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    finally:
        script_path.unlink(missing_ok=True)

    assert proc.returncode == 0, (
        f"Node script failed (rc={proc.returncode}):\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert lines, (
        f"Expected JSON line on stdout, got empty output. STDERR:\n{proc.stderr}"
    )
    return json.loads(lines[-1])  # type: ignore[no-any-return]


_NODE_DOM_HARNESS_PREAMBLE = r"""
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const HTML_PATH = __HTML_PATH__;
const html = fs.readFileSync(HTML_PATH, 'utf8');
const scriptMatches = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scriptMatches.length, 1, 'Expected single inline <script> in tasks_dashboard.html');
const dashboardScript = scriptMatches[0][1];

function createClassList() {
  const classes = new Set();
  return {
    add(...items) { items.forEach((c) => classes.add(c)); },
    remove(...items) { items.forEach((c) => classes.delete(c)); },
    contains(c) { return classes.has(c); },
    toggle(c) {
      if (classes.has(c)) { classes.delete(c); return false; }
      classes.add(c);
      return true;
    },
    toString() { return [...classes].join(' '); },
  };
}

class FakeElement {
  constructor(tagName = 'div', id = '') {
    this.tagName = tagName.toUpperCase();
    this.id = id;
    this.style = { display: '', overflow: '', color: '' };
    this.dataset = {};
    this.attributes = {};
    this.classList = createClassList();
    this.listeners = new Map();
    this.children = [];
    this.parentNode = null;
    this._innerHTML = '';
    this.textContent = '';
    this.value = '';
    this.src = 'about:blank';
    this.scrollTop = 0;
    this.scrollLeft = 0;
    this.selectionStart = 0;
    this.selectionEnd = 0;
    this.contentWindow = null;
    this._doc = null;
  }

  set className(val) {
    this.classList = createClassList();
    String(val || '').split(/\s+/).filter(Boolean).forEach((c) => this.classList.add(c));
  }
  get className() {
    return this.classList.toString();
  }

  get firstElementChild() {
    return this.children[0] || null;
  }

  setAttribute(k, v) {
    this.attributes[k] = String(v);
    if (k === 'id') this.id = String(v);
    if (k === 'class') this.className = String(v);
    if (k.startsWith('data-')) {
      const camel = k.slice(5).replace(/-([a-z])/g, (_, ch) => ch.toUpperCase());
      this.dataset[camel] = String(v);
    }
  }
  getAttribute(k) {
    if (k === 'id') return this.id || null;
    if (k === 'class') return this.className || null;
    if (k in this.attributes) return this.attributes[k];
    if (k.startsWith('data-')) {
      const camel = k.slice(5).replace(/-([a-z])/g, (_, ch) => ch.toUpperCase());
      return camel in this.dataset ? this.dataset[camel] : null;
    }
    return null;
  }
  hasAttribute(k) { return this.getAttribute(k) !== null; }

  addEventListener(type, fn) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(fn);
  }
  dispatchEvent(evt) {
    const fns = this.listeners.get(evt.type) || [];
    evt.target = evt.target || this;
    fns.forEach((fn) => fn(evt));
  }
  focus() {
    if (this._doc) this._doc.activeElement = this;
  }
  blur() {
    if (this._doc && this._doc.activeElement === this) {
      this._doc.activeElement = this._doc.body;
    }
    this.dispatchEvent({ type: 'blur', target: this });
  }
  contains(node) {
    if (node === this) return true;
    return this.children.some((c) => c.contains(node));
  }
  appendChild(child) {
    child.parentNode = this;
    child._doc = this._doc;
    this.children.push(child);
    if (this._doc && child.id) this._doc._byId.set(child.id, child);
    return child;
  }
  replaceChild(newChild, oldChild) {
    const idx = this.children.indexOf(oldChild);
    if (idx !== -1) {
      newChild.parentNode = this;
      newChild._doc = this._doc;
      this.children[idx] = newChild;
      if (this._doc && newChild.id) this._doc._byId.set(newChild.id, newChild);
    }
    return oldChild;
  }

  set innerHTML(markup) {
    this._innerHTML = String(markup || '');
    this.children = [];
    if (!this._doc) return;
    const cleanHtml = this._innerHTML.replace(/<!--[\s\S]*?-->/g, '');
    const voidTags = new Set(['input', 'br', 'hr', 'img', 'meta', 'link']);
    const tokenRegex = /<(\/?)([a-zA-Z0-9]+)\b((?:[^>"']|"[^"]*"|'[^']*')*)>/g;
    const stack = [{ el: this, tag: this.tagName.toLowerCase(), innerStart: 0 }];
    let m;
    while ((m = tokenRegex.exec(cleanHtml)) !== null) {
      const isClose = m[1] === '/';
      const tag = m[2].toLowerCase();
      const attrsRaw = m[3] || '';
      if (isClose) {
        for (let idx = stack.length - 1; idx >= 1; idx--) {
          if (stack[idx].tag === tag) {
            while (stack.length - 1 >= idx) {
              const popped = stack.pop();
              popped.el._innerHTML = cleanHtml.slice(popped.innerStart, m.index);
            }
            break;
          }
        }
        continue;
      }
      const parentEntry = stack[stack.length - 1];
      const child = new FakeElement(tag);
      child._doc = this._doc;
      child.parentNode = parentEntry.el;
      const attrRegex = /([a-zA-Z0-9_-]+)="([^"]*)"/g;
      let am;
      while ((am = attrRegex.exec(attrsRaw)) !== null) {
        child.setAttribute(am[1], am[2]);
      }
      if (tag === 'option' && /\bselected\b/.test(attrsRaw)) {
        for (let sIdx = stack.length - 1; sIdx >= 0; sIdx--) {
          if (stack[sIdx].tag === 'select') {
            stack[sIdx].el.value = 'value' in child.attributes ? child.attributes.value : '';
            break;
          }
        }
      }
      parentEntry.el.children.push(child);
      if (child.id) this._doc._byId.set(child.id, child);
      if (!voidTags.has(tag) && !/\/\s*$/.test(attrsRaw)) {
        stack.push({ el: child, tag, innerStart: m.index + m[0].length });
      }
    }
  }
  get innerHTML() {
    return this._innerHTML;
  }

  querySelectorAll(selector) {
    const results = [];
    const matchFn = (el) => {
      if (selector.startsWith('.')) {
        return el.classList.contains(selector.slice(1));
      }
      if (selector.startsWith('[') && selector.endsWith(']')) {
        return el.hasAttribute(selector.slice(1, -1));
      }
      return el.tagName.toLowerCase() === selector.toLowerCase();
    };
    const visit = (node) => {
      for (const ch of node.children) {
        if (matchFn(ch)) results.push(ch);
        visit(ch);
      }
    };
    visit(this);
    return results;
  }
}

function createFakeDomHarness(fetchHandler) {
  const storage = new Map();
  const body = new FakeElement('body');
  const documentElement = new FakeElement('html');
  const doc = {
    _byId: new Map(),
    body,
    documentElement,
    activeElement: body,
    _listeners: new Map(),
    createElement(tag) {
      const el = new FakeElement(tag);
      el._doc = doc;
      return el;
    },
    getElementById(id) {
      return doc._byId.get(id) || null;
    },
    querySelectorAll(selector) {
      return body.querySelectorAll(selector);
    },
    addEventListener(type, fn) {
      if (!doc._listeners.has(type)) doc._listeners.set(type, []);
      doc._listeners.get(type).push(fn);
    },
  };
  body._doc = doc;

  const coreIds = [
    ['div', 'metrics-summary'],
    ['div', 'stat-repos-count'],
    ['div', 'stat-epics-count'],
    ['div', 'stat-tasks-progress'],
    ['div', 'stat-worktrees-count'],
    ['nav', 'repo-tab-bar'],
    ['main', 'repo-detail-view'],
    ['div', 'repos-container'],
    ['div', 'modal-epics'],
    ['div', 'epics-modal-title'],
    ['div', 'epics-modal-body'],
    ['div', 'modal-quota'],
    ['iframe', 'quota-iframe'],
    ['div', 'quota-loading-msg'],
    ['div', 'toast'],
    ['span', 'toast-icon'],
    ['span', 'toast-text'],
  ];
  for (const [tag, id] of coreIds) {
    const el = doc.createElement(tag);
    el.id = id;
    if (id.startsWith('modal-')) el.className = 'modal-backdrop';
    el.style.display = 'none';
    body.appendChild(el);
  }

  const postedMessages = [];
  const quotaIframe = doc.getElementById('quota-iframe');
  quotaIframe.contentWindow = {
    postMessage(msg, targetOrigin) {
      postedMessages.push({ msg, targetOrigin });
    },
  };

  const windowObj = {
    location: { protocol: 'http:', port: '8766', origin: 'http://127.0.0.1:8766', href: 'http://127.0.0.1:8766/' },
    scrollY: 0,
    scrollX: 0,
    scrollTo() {},
    addEventListener() {},
    getComputedStyle(el) {
      return { display: el?.style?.display || 'none' };
    },
    open() {},
  };

  const sandbox = {
    window: windowObj,
    document: doc,
    localStorage: {
      getItem(k) { return storage.has(k) ? storage.get(k) : null; },
      setItem(k, v) { storage.set(k, String(v)); },
      removeItem(k) { storage.delete(k); },
    },
    navigator: { clipboard: { writeText: async () => {} } },
    fetch: fetchHandler,
    URL,
    Event: class Event { constructor(type) { this.type = type; } },
    setTimeout(fn, delay) {
      // Skip automatic initDashboard bootstrap timer; execute 0..150ms UI refresh timers immediately if safe
      if (fn && fn.name === 'initDashboard') return 0;
      if (delay <= 100 && typeof fn === 'function') fn();
      return 0;
    },
    clearTimeout() {},
    setInterval() { return 0; },
    clearInterval() {},
    console,
    Math,
    JSON,
    Date,
    Set,
    Map,
    Array,
    Object,
    String,
    Number,
    Boolean,
    RegExp,
    Error,
    Promise,
  };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(dashboardScript, sandbox);
  return { sandbox, doc, windowObj, postedMessages };
}
"""

_NODE_CDP_HELPER = r"""
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';

export async function launchHeadlessChromeCdp(chromeBin) {
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'rsdh-cdp-'));
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
    if (msg.method === 'Runtime.consoleAPICalled' && msg.params?.type === 'error') {
      const text = (msg.params.args || []).map((a) => a.value ?? a.description ?? '').join(' ');
      consoleErrors.push(text);
    }
    if (msg.method === 'Runtime.exceptionThrown') {
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

  async function evaluate(expression) {
    const res = await send('Runtime.evaluate', {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    if (res.exceptionDetails) {
      throw new Error(`Page evaluation failed: ${JSON.stringify(res.exceptionDetails)}`);
    }
    return res.result?.value;
  }

  async function close() {
    try { ws.close(); } catch (_) {}
    if (!chrome.killed && chrome.exitCode === null) {
      chrome.kill('SIGTERM');
    }
    const forceTimer = setTimeout(() => {
      if (chrome.exitCode === null) {
        try { chrome.kill('SIGKILL'); } catch (_) {}
      }
    }, 3000);
    await exitPromise;
    clearTimeout(forceTimer);
    fs.rmSync(userDataDir, { recursive: true, force: true });
  }

  await send('Page.enable');
  await send('Runtime.enable');
  return { send, evaluate, close, consoleErrors, runtimeExceptions };
}
"""


class _MutableTasksServer(http.server.ThreadingHTTPServer):
    """Lightweight HTTP server serving real tasks_dashboard.html with mutable /api/tasks."""

    def __init__(self, initial_payload: dict[str, Any]) -> None:
        self.payload = initial_payload
        self.pic_posts: list[dict[str, Any]] = []
        port = find_available_port(19850)

        server_ref = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                return

            def _send_json(self, code: int, data: Any) -> None:
                raw = json.dumps(data).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self) -> None:
                if self.path == "/" or self.path.startswith("/?"):
                    content = DASHBOARD_HTML.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(content)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(content)
                    return
                if self.path == "/api/tasks":
                    self._send_json(200, server_ref.payload)
                    return
                if self.path == "/api/profiles":
                    self._send_json(200, {"profiles": ["brother", "tess", "danhdue"]})
                    return
                self.send_error(404)

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                data = json.loads(raw.decode("utf-8"))
                if self.path == "/api/epic/pic":
                    server_ref.pic_posts.append(data)
                    pic = data.get("pic", "")
                    epic = data.get("epic", "")
                    for repo in server_ref.payload.get("repos", []):
                        if repo.get("name") == data.get("repo"):
                            if repo.get("active_epic") == epic:
                                repo["account_id"] = pic
                            for ep in repo.get("epics_summary", {}).get("epics", []):
                                if ep.get("slug") == epic:
                                    ep["pic"] = pic
                    self._send_json(
                        200,
                        {"status": "ok", "updated_files": ["handoff.md"]},
                    )
                    return
                if self.path == "/api/launch/quota":
                    self._send_json(
                        200,
                        {"status": "ok", "url": "http://127.0.0.1:8765"},
                    )
                    return
                self.send_error(404)

        super().__init__(("127.0.0.1", port), Handler)


def _sample_repo_payload(
    *,
    account_id: str = "brother",
    prompt: str = "Running Gate 4 verification",
    active_stage: str = "Stage 3 Phase 4 (Review)",
    is_human_action_required: bool = False,
    done_count: int = 5,
    total_count: int = 5,
    epic_status: str = "in_progress",
    is_review_converged: bool = False,
    heartbeat: dict[str, Any] | None = None,
    quality_active: dict[str, Any] | None = None,
    pending_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tasks = []
    for idx in range(1, total_count + 1):
        tasks.append(
            {
                "id": f"task_{idx:02d}",
                "title": f"Task {idx}",
                "status": "done" if idx <= done_count else "in-progress",
                "priority": "high",
                "epic": "demo-epic",
            }
        )
    pct = round((done_count / total_count) * 100) if total_count > 0 else 0
    return {
        "workspace_root": "/tmp/ws",
        "scanned_at": "2026-11-13T10:00:00Z",
        "available_profiles": ["brother", "tess", "danhdue"],
        "repos": [
            {
                "name": "ai-agent-tools",
                "path": "/tmp/ws/ai-agent-tools",
                "theme_color": "#b45309",
                "window_title": "ai-agent-tools",
                "active_epic": "demo-epic",
                "active_stage": active_stage,
                "account_id": account_id,
                "prompt": prompt,
                "is_human_action_required": is_human_action_required,
                "pending_decision": pending_decision,
                "heartbeat": heartbeat,
                "quality_active": quality_active,
                "quality_runs": [quality_active] if quality_active else [],
                "worktrees": [
                    {
                        "path": "/tmp/ws/ai-agent-tools",
                        "branch": "main",
                        "is_dirty": False,
                        "dirty_file_count": 0,
                    },
                    {
                        "path": "/tmp/ws/ai-agent-tools/.worktrees/demo-epic",
                        "branch": "epic/demo-epic",
                        "is_dirty": False,
                        "dirty_file_count": 0,
                    },
                ],
                "task_progress": {
                    "total_tasks": total_count,
                    "done_tasks": done_count,
                    "in_progress_tasks": total_count - done_count,
                    "todo_tasks": 0,
                    "percentage": pct,
                    "active_task_name": "task_05"
                    if done_count < total_count
                    else "All tasks done",
                    "tasks": tasks,
                },
                "epics_summary": {
                    "total": 2,
                    "completed": 1 if epic_status == "done" else 0,
                    "in_progress": 0 if epic_status == "done" else 1,
                    "unstarted": 1,
                    "abandoned": 0,
                    "epics": [
                        {
                            "slug": "demo-epic",
                            "title": "Demo Epic",
                            "status": epic_status,
                            "pic": account_id,
                            "task_count": total_count,
                            "mtime": 1794550000.0,
                            "last_updated": "2026-11-13T09:00:00Z",
                            "last_updated_human": "1h",
                            "is_review_converged": is_review_converged,
                            "is_action_required": is_human_action_required,
                        },
                        {
                            "slug": "sibling-backlog",
                            "title": "Sibling Backlog",
                            "status": "unstarted",
                            "pic": "danhdue",
                            "task_count": 2,
                            "mtime": 1794540000.0,
                            "last_updated": "2026-11-13T06:00:00Z",
                            "last_updated_human": "4h",
                        },
                    ],
                },
            }
        ],
    }


def _git_init_with_commit(repo_path: Path) -> None:
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=repo_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Tester"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    (repo_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "[TEST] Init repo"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )


def test_rsdh_hp_07_96_cap_and_tier2_live_sync() -> None:
    """[RSDH-HP-07] [Tier C - Integration] Tasks dashboard enforces 96% pre-finish ceiling and refreshes Section II live on state changes."""
    # Part A: Fast Node extracted-script DOM verification
    preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
        "__HTML_PATH__", json.dumps(str(DASHBOARD_HTML))
    )
    node_script = (
        preamble
        + r"""
const stripStyles = (s) => String(s).replace(/style="[^"]*"/g, '');
const payloads = """
        + json.dumps(
            [
                _sample_repo_payload(
                    account_id="brother",
                    prompt="Running Gate 4 verification",
                    heartbeat={
                        "active_wave": 1,
                        "last_event": "wave 1 started",
                        "slots": {"1": {"task_id": "task_05", "status": "working"}},
                    },
                    quality_active=None,
                ),
                _sample_repo_payload(
                    account_id="tess",
                    prompt="Running Gate 4 verification",
                    heartbeat={"active_wave": 1, "last_event": "wave 1 started"},
                    quality_active=None,
                ),
                _sample_repo_payload(
                    account_id="tess",
                    prompt="Approve Gate 4 Triage",
                    is_human_action_required=True,
                    pending_decision={
                        "decision_id": "dec-1",
                        "active": True,
                        "epic": "demo-epic",
                        "reason": "Approve Gate 4 Triage",
                    },
                    heartbeat={"active_wave": 1, "last_event": "wave 1 paused"},
                    quality_active=None,
                ),
                _sample_repo_payload(
                    account_id="tess",
                    prompt="Running quality gate",
                    is_human_action_required=False,
                    heartbeat={
                        "active_wave": 2,
                        "last_event": "wave 2 active",
                        "slots": {"2": {"task_id": "task_06", "status": "working"}},
                    },
                    quality_active={
                        "run_id": "run-1",
                        "epic_slug": "demo-epic",
                        "status": "running",
                        "provider": "python-qa",
                        "capability": "test",
                        "step_index": 2,
                        "step_total": 4,
                        "elapsed_sec": 14,
                    },
                ),
                _sample_repo_payload(
                    account_id="tess",
                    prompt="Stale quality ignored",
                    is_human_action_required=False,
                    heartbeat=None,
                    quality_active={
                        "run_id": "run-stale",
                        "epic_slug": "demo-epic",
                        "status": "stale",
                        "provider": "python-qa",
                        "step_index": 1,
                        "step_total": 4,
                    },
                ),
            ]
        )
        + r""";

let pollIdx = 0;
const { sandbox, doc } = createFakeDomHarness(async (url) => ({
  async json() {
    if (String(url).includes('/api/tasks')) {
      const idx = Math.min(pollIdx, payloads.length - 1);
      return payloads[idx];
    }
    return {};
  },
}));

assert.equal(typeof sandbox.pollDashboard, 'function', 'pollDashboard must be exposed');

// Initial poll (5/5 tasks done pre-convergence)
await sandbox.pollDashboard();
const tier2El = doc.getElementById('tier2-execution-epics-wrapper-ai-agent-tools');
const kanbanEl = doc.getElementById('kanban-dashboard-wrapper-ai-agent-tools');
assert.ok(tier2El, 'Tier 2 wrapper rendered');
assert.ok(kanbanEl, 'Kanban wrapper rendered');

assert.match(kanbanEl.innerHTML, /92%/, 'Section I must display 92% weighted review progress pre-finish');
assert.match(kanbanEl.innerHTML, /92% Review/, 'Section I must display 92% Review');
assert.doesNotMatch(kanbanEl.innerHTML, /width:\s*(?:99|100)%/, 'Section I lifecycle bar must not display 99% or 100% pre-convergence');

assert.match(tier2El.innerHTML, /92%/, 'Section II must display 92% weighted review progress pre-finish');
assert.match(tier2El.innerHTML, /92% Review/, 'Section II must display 92% Review');
assert.doesNotMatch(tier2El.innerHTML, /width:\s*(?:99|100)%/, 'Section II lifecycle bar must not display 99% or 100% pre-convergence');
const initialSig = tier2El.dataset.sig;

// Poll 1 -> 1 (account_id change)
pollIdx = 1;
await sandbox.pollDashboard();
assert.notEqual(tier2El.dataset.sig, initialSig, 'tier2Sig must detect account_id update');
assert.match(tier2El.innerHTML, /@tess/, 'Section II must re-render updated account_id');
const sigAfterPic = tier2El.dataset.sig;

// Poll 2 (prompt + is_human_action_required + pending_decision)
pollIdx = 2;
await sandbox.pollDashboard();
assert.notEqual(tier2El.dataset.sig, sigAfterPic, 'tier2Sig must detect prompt/pending_decision update');
assert.match(tier2El.innerHTML, /Approve Gate 4 Triage/, 'Section II must display updated pending decision/prompt');
const sigAfterDecision = tier2El.dataset.sig;

// Poll 3 (heartbeat wave 2 + quality_active running)
pollIdx = 3;
await sandbox.pollDashboard();
assert.notEqual(tier2El.dataset.sig, sigAfterDecision, 'tier2Sig must detect heartbeat & quality_active update');
assert.match(tier2El.innerHTML, /Wave 2/, 'Section II must display active heartbeat wave');
assert.match(tier2El.innerHTML, /wave 2 active/, 'Section II must display heartbeat last_event');
assert.match(tier2El.innerHTML, /python-qa/, 'Section II must display running quality provider');
assert.match(tier2El.innerHTML, /2\/4/, 'Section II must display running quality step progress');

// Poll 4 (absent heartbeat + stale quality run -> zero errors, no running banner)
pollIdx = 4;
await sandbox.pollDashboard();
assert.doesNotMatch(tier2El.innerHTML, /Quality Running/, 'Stale quality run must not render running banner');

console.log(JSON.stringify({ status: 'ok', finalSig: tier2El.dataset.sig }));
"""
    )
    node_res = _run_node_script(node_script)
    assert node_res["status"] == "ok"


class TestTasksDashboard_Integration:
    """Integration runner suite verifying real Chrome CDP and live server DOM behavior."""

    def test_rsdh_hp_07_chrome_cdp_integration(self, tmp_path: Path) -> None:
        """[RSDH-HP-07] [Tier C - Integration] Tasks dashboard enforces 96% ceiling and refreshes Section II live in Chrome CDP."""
        chrome_bin = _resolve_chrome_binary()
        initial_payload = _sample_repo_payload(
            account_id="brother",
            prompt="Running Gate 4 verification",
            heartbeat={"active_wave": 1, "last_event": "wave 1 init"},
            quality_active=None,
        )
        server = _MutableTasksServer(initial_payload)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        url = f"http://127.0.0.1:{server.server_port}/"

        (tmp_path / "cdp_helper.mjs").write_text(_NODE_CDP_HELPER, encoding="utf-8")

        # Local control endpoint mutates server payload directly from Chrome test script
        updated_payload = _sample_repo_payload(
            account_id="tess",
            prompt="Live Gate 4 Check",
            heartbeat={
                "active_wave": 2,
                "last_event": "slot 2 running",
                "slots": {"2": {"task_id": "task_05", "status": "working"}},
            },
            quality_active={
                "run_id": "r2",
                "epic_slug": "demo-epic",
                "status": "running",
                "provider": "python-qa",
                "capability": "test",
                "step_index": 3,
                "step_total": 4,
                "elapsed_sec": 9,
            },
        )
        server.payload_next = updated_payload  # type: ignore[attr-defined]

        class _ControlHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                return

            def do_POST(self) -> None:
                server.payload = updated_payload
                self.send_response(200)
                self.end_headers()

        ctrl_port = find_available_port(19920)
        ctrl_server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", ctrl_port), _ControlHandler
        )
        threading.Thread(target=ctrl_server.serve_forever, daemon=True).start()

        cdp_test_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(tmp_path / "cdp_helper.mjs"))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Page.navigate', {{ url: {json.dumps(url)} }});
  let ready = false;
  for (let i = 0; i < 40; i++) {{
    ready = await cdp.evaluate(`Boolean(document.querySelector('#tier2-execution-epics-wrapper-ai-agent-tools .epic-execution-item'))`);
    if (ready) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.ok(ready, 'Dashboard must render initial Tier 2 card in Chrome CDP');
  await cdp.evaluate(`window.__rsdhNoReloadMarker = 'alive'`);

  const sec1Before = await cdp.evaluate(`document.getElementById('kanban-dashboard-wrapper-ai-agent-tools').innerText`);
  const sec2Before = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  assert.match(sec1Before, /92% Review/);
  assert.doesNotMatch(sec1Before, /99%|100% ✓ Done|100% ⚠️/);
  assert.match(sec2Before, /92% Review/);
  assert.doesNotMatch(sec2Before, /99%|100% ✓ Done|100% ⚠️/);

  const mutRes = await fetch({json.dumps(f"http://127.0.0.1:{ctrl_port}/mutate")}, {{ method: 'POST' }});
  assert.equal(mutRes.status, 200);

  await cdp.evaluate(`pollDashboard()`);
  const sec2After = await cdp.evaluate(`document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText`);
  const marker = await cdp.evaluate(`window.__rsdhNoReloadMarker`);

  assert.equal(marker, 'alive', 'Must update Section II without reloading page');
  assert.match(sec2After, /@tess/);
  assert.match(sec2After, /Wave 2/);
  assert.match(sec2After, /python-qa/);
  assert.match(sec2After, /3\/4/);
  assert.match(sec2After, /85%/);
  assert.match(sec2After, /100%/);
  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok', marker, sec2After }}));
}} finally {{
  await cdp.close();
}}
"""
        try:
            cdp_res = _run_node_script(cdp_test_script, timeout=45)
            assert cdp_res["status"] == "ok"
        finally:
            ctrl_server.shutdown()
            ctrl_server.server_close()
            server.shutdown()
            server.server_close()

    def test_rsdh_ec_06_roadmap_no_subday_mtime_and_focus_chrome_cdp(
        self, tmp_path: Path
    ) -> None:
        """[RSDH-EC-06] [Tier C - Integration] Roadmap eliminates sub-day mtime sorting and preserves native select focus in Chrome CDP."""
        # Part A: Node verification of sortEpicsForRoadmap (no mtime), data-row-key, roadmapSig, modal-epics style.display, and quota ?embedded=1/postMessage
        preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
            "__HTML_PATH__", json.dumps(str(DASHBOARD_HTML))
        )
        node_script = (
            preamble
            + r"""
let picPosts = [];
const repoSnapshot = {
  name: 'ai-agent-tools',
  path: '/tmp/ws/ai-agent-tools',
  theme_color: '#b45309',
  active_epic: 'active-epic',
  active_stage: 'Stage 3 Phase 2 (TDD)',
  account_id: 'brother',
  prompt: 'Implementing',
  is_human_action_required: false,
  worktrees: [],
  task_progress: { total_tasks: 1, done_tasks: 0, in_progress_tasks: 1, todo_tasks: 0, percentage: 0, tasks: [] },
  epics_summary: {
    total: 3,
    completed: 0,
    in_progress: 1,
    unstarted: 2,
    abandoned: 0,
    epics: [
      { slug: 'active-epic', title: 'Active', status: 'in_progress', pic: 'brother', task_count: 1, mtime: 1794500000, last_updated: '2026-11-12T08:00:00Z', last_updated_human: '1d' },
      { slug: 'alpha-backlog', title: 'Alpha', status: 'unstarted', pic: 'brother', task_count: 2, mtime: 1794530000, last_updated: '2026-11-13T01:00:00Z', last_updated_human: '8h' },
      { slug: 'beta-backlog', title: 'Beta', status: 'unstarted', pic: 'danhdue', task_count: 2, mtime: 1794560000, last_updated: '2026-11-13T09:00:00Z', last_updated_human: '1h' },
    ],
  },
};

const { sandbox, doc, postedMessages } = createFakeDomHarness(async (url, opts) => {
  if (String(url).includes('/api/epic/pic')) {
    picPosts.push(JSON.parse(opts.body));
    return { async json() { return { status: 'ok', updated_files: ['handoff.md'] }; } };
  }
  if (String(url).includes('/api/launch/quota')) {
    return { async json() { return { status: 'ok', url: 'http://127.0.0.1:8765/?tab=limits' }; } };
  }
  if (String(url).includes('/api/tasks')) {
    return { async json() { return { available_profiles: ['brother', 'tess', 'danhdue'], repos: [repoSnapshot] }; } };
  }
  return { async json() { return {}; } };
});

// 1. Verify sortEpicsForRoadmap does not use mtime
const sortFnSrc = sandbox.sortEpicsForRoadmap.toString();
assert.equal(/\bmtime\b/.test(sortFnSrc), false, 'sortEpicsForRoadmap must remove sub-day mtime sorting completely');

const sortedBefore = Array.from(sandbox.sortEpicsForRoadmap(repoSnapshot.epics_summary.epics, 'active-epic')).map((e) => e.slug);
assert.deepEqual(sortedBefore, ['active-epic', 'alpha-backlog', 'beta-backlog']);

// Bump alpha-backlog mtime higher than beta-backlog on the same day -> order must remain identical
repoSnapshot.epics_summary.epics[1].mtime = 1794599999;
repoSnapshot.epics_summary.epics[1].last_updated = '2026-11-13T23:55:00Z';
const sortedAfter = Array.from(sandbox.sortEpicsForRoadmap(repoSnapshot.epics_summary.epics, 'active-epic')).map((e) => e.slug);
assert.deepEqual(sortedAfter, sortedBefore, 'Same-day mtime bumps must never reorder Roadmap rows');

// 2. Verify data-row-key & mount/poll roadmapSig alignment
await sandbox.pollDashboard();
const roadmapTbody = doc.getElementById('roadmap-tbody-ai-agent-tools');
assert.ok(roadmapTbody, 'Roadmap tbody rendered');
const rowKeys = Array.from(roadmapTbody.querySelectorAll('.roadmap-epic-row')).map((r) => r.getAttribute('data-row-key'));
assert.deepEqual(rowKeys, ['ai-agent-tools:active-epic', 'ai-agent-tools:alpha-backlog', 'ai-agent-tools:beta-backlog']);
const selectKeys = Array.from(roadmapTbody.querySelectorAll('.select-pic-roadmap')).map((s) => s.getAttribute('data-row-key'));
assert.deepEqual(selectKeys, ['ai-agent-tools:active-epic', 'ai-agent-tools:alpha-backlog', 'ai-agent-tools:beta-backlog']);

// 3. Verify updateEpicPic checks #modal-epics via style.display === 'flex' (not .classList.contains('active'))
const modalEpics = doc.getElementById('modal-epics');
modalEpics.style.display = 'flex';
let openEpicsCalls = 0;
const origOpenEpics = sandbox.openEpicsModal;
sandbox.openEpicsModal = function(repoName) {
  openEpicsCalls++;
  return origOpenEpics(repoName);
};
sandbox.updateEpicPic('ai-agent-tools', 'alpha-backlog', 'tess');
await new Promise((r) => setTimeout(r, 20));
assert.equal(openEpicsCalls, 1, 'updateEpicPic must refresh #modal-epics when style.display === flex');
assert.equal(picPosts.length, 1);

// Verify does NOT refresh when modal-epics is hidden even if stale .active class exists
modalEpics.style.display = 'none';
modalEpics.classList.add('active');
sandbox.updateEpicPic('ai-agent-tools', 'beta-backlog', 'tess');
await new Promise((r) => setTimeout(r, 20));
assert.equal(openEpicsCalls, 1, 'updateEpicPic must NOT rely on stale .classList.contains(active)');

// 4. Verify openQuotaModal, refreshQuotaIframe, and closeLiveModal quota ?embedded=1 & postMessage
const iframe = doc.getElementById('quota-iframe');
sandbox.openQuotaModal();
await new Promise((r) => setTimeout(r, 20));
assert.equal(iframe.src, 'http://127.0.0.1:8765/?tab=limits&embedded=1');
assert.ok(
  postedMessages.some((m) => m.msg && m.msg.action === 'reset_quota_submodals'),
  'openQuotaModal must post reset_quota_submodals to #quota-iframe',
);

const msgCountAfterOpen = postedMessages.length;
sandbox.refreshQuotaIframe();
assert.equal(iframe.src, 'http://127.0.0.1:8765/?tab=limits&embedded=1');
sandbox.closeLiveModal('modal-quota');
assert.ok(
  postedMessages.slice(msgCountAfterOpen).some((m) => m.msg && m.msg.action === 'reset_quota_submodals'),
  'closeLiveModal(modal-quota) must post reset_quota_submodals to #quota-iframe',
);

console.log(JSON.stringify({ status: 'ok', rowKeys, openEpicsCalls }));
"""
        )
        node_res = _run_node_script(node_script)
        assert node_res["status"] == "ok"

        # Part B: Real headless Chrome CDP test against REAL unmodified TasksServer + real git repo with same-day distinct mtimes
        chrome_bin = _resolve_chrome_binary()
        ws_root = tmp_path / "ws"
        repo_dir = ws_root / "ai-agent-tools"
        epic_alpha = repo_dir / ".devtool" / "epic" / "epic-alpha"
        epic_beta = repo_dir / ".devtool" / "epic" / "epic-beta"
        epic_alpha.mkdir(parents=True)
        epic_beta.mkdir(parents=True)
        _git_init_with_commit(repo_dir)

        (epic_alpha / "epic-alpha.en.md").write_text(
            "# Epic Alpha\n\n- **Status**: unstarted\n- **PIC**: brother\n",
            encoding="utf-8",
        )
        (epic_alpha / "task_01_alpha.md").write_text(
            "---\nid: task_01_alpha\nstatus: todo\n---\n# Alpha Task 1\n",
            encoding="utf-8",
        )
        (epic_beta / "epic-beta.en.md").write_text(
            "# Epic Beta\n\n- **Status**: unstarted\n- **PIC**: danhdue\n",
            encoding="utf-8",
        )
        (epic_beta / "task_01_beta.md").write_text(
            "---\nid: task_01_beta\nstatus: todo\n---\n# Beta Task 1\n",
            encoding="utf-8",
        )

        # Set distinct same-day UTC mtimes: epic-alpha older (01:00 UTC), epic-beta newer (08:00 UTC)
        today_utc = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        t_alpha = today_utc.replace(hour=1).timestamp()
        t_beta = today_utc.replace(hour=8).timestamp()
        for path_item in epic_alpha.iterdir():
            os.utime(path_item, (t_alpha, t_alpha))
        os.utime(epic_alpha, (t_alpha, t_alpha))
        for path_item in epic_beta.iterdir():
            os.utime(path_item, (t_beta, t_beta))
        os.utime(epic_beta, (t_beta, t_beta))

        pid_file = tmp_path / "tasks_server.pid"
        port = find_available_port(19870)
        server = TasksServer(
            host="127.0.0.1",
            port=port,
            workspace_root=ws_root,
            pid_file=pid_file,
        )
        threading.Thread(target=server.serve_forever, daemon=True).start()
        time.sleep(0.1)

        (tmp_path / "cdp_helper.mjs").write_text(_NODE_CDP_HELPER, encoding="utf-8")

        # Control endpoint to bump epic-beta's same-day mtime + add a task while Chrome select holds focus
        class _BumpBetaHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                return

            def do_POST(self) -> None:
                t_beta_newer = today_utc.replace(hour=14, minute=30).timestamp()
                task2 = epic_beta / "task_02_beta.md"
                task2.write_text(
                    "---\nid: task_02_beta\nstatus: todo\n---\n# Beta Task 2\n",
                    encoding="utf-8",
                )
                for path_item in epic_beta.iterdir():
                    os.utime(path_item, (t_beta_newer, t_beta_newer))
                os.utime(epic_beta, (t_beta_newer, t_beta_newer))
                self.send_response(200)
                self.end_headers()

        bump_port = find_available_port(19940)
        bump_server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", bump_port), _BumpBetaHandler
        )
        threading.Thread(target=bump_server.serve_forever, daemon=True).start()

        url = f"http://127.0.0.1:{server.server_port}/"
        cdp_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(tmp_path / "cdp_helper.mjs"))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Page.navigate', {{ url: {json.dumps(url)} }});
  let ready = false;
  for (let i = 0; i < 40; i++) {{
    ready = await cdp.evaluate(`document.querySelectorAll('#roadmap-tbody-ai-agent-tools .roadmap-epic-row').length === 2`);
    if (ready) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.ok(ready, 'Roadmap rows must render from live TasksServer');

  const initialKeys = await cdp.evaluate(`Array.from(document.querySelectorAll('#roadmap-tbody-ai-agent-tools .roadmap-epic-row')).map(r => r.getAttribute('data-row-key'))`);
  assert.deepEqual(initialKeys, ['ai-agent-tools:epic-alpha', 'ai-agent-tools:epic-beta'], 'Alphabetical tie-breaker must ignore newer sub-day mtime on epic-beta');

  // Focus native select on epic-alpha and capture exact DOM node reference
  const focused = await cdp.evaluate(`(() => {{
    const sel = document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap[data-row-key="ai-agent-tools:epic-alpha"]');
    if (!sel) return false;
    sel.focus();
    window.__heldSelect = sel;
    return document.activeElement === sel;
  }})()`);
  assert.equal(focused, true, 'Native select must hold document.activeElement');

  // Bump epic-beta mtime & task count on disk while select holds focus, then poll
  const bumpResp = await fetch({json.dumps(f"http://127.0.0.1:{bump_port}/bump")}, {{ method: 'POST' }});
  assert.equal(bumpResp.status, 200);
  await cdp.evaluate(`pollDashboard()`);

  const focusPreserved = await cdp.evaluate(`(() => {{
    const sel = document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap[data-row-key="ai-agent-tools:epic-alpha"]');
    return {{
      sameNode: sel === window.__heldSelect,
      isActive: document.activeElement === window.__heldSelect,
      keys: Array.from(document.querySelectorAll('#roadmap-tbody-ai-agent-tools .roadmap-epic-row')).map(r => r.getAttribute('data-row-key')),
    }};
  }})()`);
  assert.equal(focusPreserved.sameNode, true, 'Focused select node must NOT be replaced during active focus');
  assert.equal(focusPreserved.isActive, true, 'document.activeElement must stay on focused select');
  assert.deepEqual(focusPreserved.keys, ['ai-agent-tools:epic-alpha', 'ai-agent-tools:epic-beta']);

  // Select a new PIC ('tess') while focused, then blur -> queued update flushes without dropping 'tess'
  await cdp.evaluate(`(() => {{
    const sel = window.__heldSelect;
    sel.value = 'tess';
    sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
    sel.blur();
  }})()`);
  // Wait for POST /api/epic/pic + queued flush
  let alphaPic = null;
  let betaCount = null;
  for (let i = 0; i < 30; i++) {{
    const state = await cdp.evaluate(`(() => {{
      const a = document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap[data-row-key="ai-agent-tools:epic-alpha"]')?.value;
      const bCells = document.querySelectorAll('#roadmap-tbody-ai-agent-tools tr[data-row-key="ai-agent-tools:epic-beta"] td');
      return {{ a, bCount: bCells[3]?.textContent?.trim() }};
    }})()`);
    alphaPic = state.a;
    betaCount = state.bCount;
    if (alphaPic === 'tess' && betaCount === '2') break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.equal(alphaPic, 'tess', 'Queued flush after blur must preserve user-selected PIC');
  assert.equal(betaCount, '2', 'Queued Roadmap poll update (task count 2) must flush after blur');

  // Verify #modal-epics visibility detection via computed style.display === 'flex'
  await cdp.evaluate(`openEpicsModal('ai-agent-tools')`);
  const modalFlex = await cdp.evaluate(`getComputedStyle(document.getElementById('modal-epics')).display`);
  assert.equal(modalFlex, 'flex');

  await cdp.evaluate(`updateEpicPic('ai-agent-tools', 'epic-beta', 'brother')`);
  let modalBetaPic = null;
  for (let i = 0; i < 30; i++) {{
    modalBetaPic = await cdp.evaluate(`document.querySelector('#epics-modal-body select.select-pic-roadmap[data-row-key="ai-agent-tools:epic-beta"]')?.value`);
    if (modalBetaPic === 'brother') break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.equal(modalBetaPic, 'brother', 'updateEpicPic must refresh #modal-epics rows cleanly via display === flex');

  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok', alphaPic, betaCount, modalBetaPic }}));
}} finally {{
  await cdp.close();
}}
"""
        try:
            cdp_res = _run_node_script(cdp_script, timeout=45)
            assert cdp_res["status"] == "ok"
        finally:
            bump_server.shutdown()
            bump_server.server_close()
            server.shutdown()
            server.server_close()

    def test_rsdh_st_05_progress_transitions(self) -> None:
        """[RSDH-ST-05] [Tier C - Integration] Progress calculation enforces 75% mid-epic, 95% in-progress cap, 96% pre-finish cap, and 100% finished state."""
        preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
            "__HTML_PATH__", json.dumps(str(DASHBOARD_HTML))
        )
        scenarios = {
            "mid_75": _sample_repo_payload(done_count=3, total_count=4)["repos"][0],
            "high_cap_95": _sample_repo_payload(done_count=39, total_count=40)["repos"][
                0
            ],
            "pre_finish_96": _sample_repo_payload(
                done_count=4, total_count=4, is_review_converged=False
            )["repos"][0],
            "waiting_finish_100": _sample_repo_payload(
                done_count=4,
                total_count=4,
                active_stage="Stage 3 Phase 4.1 (Sign-off)",
                is_human_action_required=True,
                prompt="Phê duyệt Gate 5 (Kanban Sign-off) và kết thúc nhánh (/finish)",
                is_review_converged=True,
            )["repos"][0],
            "done_100": _sample_repo_payload(
                done_count=4,
                total_count=4,
                epic_status="done",
                active_stage="Idle",
                is_review_converged=False,
            )["repos"][0],
        }

        node_script = (
            preamble
            + rf"""
const stripStyles = (s) => String(s).replace(/style="[^"]*"/g, '');
const scenarios = {json.dumps(scenarios)};
const {{ sandbox }} = createFakeDomHarness(async () => ({{ async json() {{ return {{}}; }} }}));

// 1. 3/4 done -> 66% weighted lifecycle progress + 75% task completion
const s1 = sandbox.renderKanbanDashboard(scenarios.mid_75, 'all');
const e1 = sandbox.renderExecutionEpics(scenarios.mid_75);
assert.match(s1, /66%/);
assert.match(s1, /75%/);
assert.match(e1, /66%/);
assert.match(e1, /75%/);

// 2. 39/40 done -> capped at 79% weighted lifecycle progress (never 98/99/100)
const s2 = sandbox.renderKanbanDashboard(scenarios.high_cap_95, 'all');
const e2 = sandbox.renderExecutionEpics(scenarios.high_cap_95);
assert.match(s2, /width:\s*79%/);
assert.doesNotMatch(s2, /width:\s*(?:98|99|100)%/);
assert.match(e2, /79%/);
assert.doesNotMatch(e2, /width:\s*(?:98|99|100)%/);

// 3. 4/4 done pre-convergence -> 92% ("92% Review") + 100% task completion
const s3 = sandbox.renderKanbanDashboard(scenarios.pre_finish_96, 'all');
const e3 = sandbox.renderExecutionEpics(scenarios.pre_finish_96);
assert.match(s3, /width:\s*92%/);
assert.match(s3, /92% Review/);
assert.doesNotMatch(s3, /width:\s*(?:98|99|100)%/);
assert.match(e3, /92%/);
assert.match(e3, /92% Review/);
assert.match(e3, /100%/);
assert.doesNotMatch(e3, /width:\s*(?:98|99|100)%/);

// 4. 4/4 done with Gate 4 Review Converged (Waiting Finish) -> 98%
const s4 = sandbox.renderKanbanDashboard(scenarios.waiting_finish_100, 'all');
const e4 = sandbox.renderExecutionEpics(scenarios.waiting_finish_100);
assert.match(s4, /98%/);
assert.match(e4, /98%/);

// 5. Gate 5 Done -> 100%
const s5 = sandbox.renderKanbanDashboard(scenarios.done_100, 'all');
const e5 = sandbox.renderExecutionEpics(scenarios.done_100);
assert.match(s5, /100%/);
assert.match(e5, /100%/);

console.log(JSON.stringify({{ status: 'ok' }}));
"""
        )
        res = _run_node_script(node_script)
        assert res["status"] == "ok"

    def test_rsdh_ar_02_live_polling_preserves_focus_and_zero_console_errors(
        self,
        tmp_path: Path,
    ) -> None:
        """[RSDH-AR-02] [Tier C - Integration] Live polling applies Tier 2 updates immediately without clobbering focused controls or emitting console errors."""
        chrome_bin = _resolve_chrome_binary()
        initial_payload = _sample_repo_payload(
            account_id="brother",
            done_count=3,
            total_count=4,
            heartbeat={"active_wave": 1, "last_event": "wave 1 starting"},
            quality_active={
                "run_id": "q1",
                "epic_slug": "demo-epic",
                "status": "running",
                "provider": "python-qa",
                "capability": "lint",
                "step_index": 1,
                "step_total": 3,
            },
        )
        server = _MutableTasksServer(initial_payload)
        threading.Thread(target=server.serve_forever, daemon=True).start()

        second_payload = _sample_repo_payload(
            account_id="brother",
            done_count=4,
            total_count=4,
            heartbeat={"active_wave": 2, "last_event": "wave 2 executing"},
            quality_active={
                "run_id": "q1",
                "epic_slug": "demo-epic",
                "status": "running",
                "provider": "python-qa",
                "capability": "test",
                "step_index": 2,
                "step_total": 3,
            },
        )
        second_payload["repos"][0]["epics_summary"]["epics"][1]["task_count"] = 5

        class _StepHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                return

            def do_POST(self) -> None:
                server.payload = second_payload
                self.send_response(200)
                self.end_headers()

        ctrl_port = find_available_port(19960)
        ctrl_server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", ctrl_port), _StepHandler
        )
        threading.Thread(target=ctrl_server.serve_forever, daemon=True).start()

        (tmp_path / "cdp_helper.mjs").write_text(_NODE_CDP_HELPER, encoding="utf-8")
        url = f"http://127.0.0.1:{server.server_port}/"
        cdp_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(tmp_path / "cdp_helper.mjs"))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Page.navigate', {{ url: {json.dumps(url)} }});
  let ready = false;
  for (let i = 0; i < 40; i++) {{
    ready = await cdp.evaluate(`Boolean(document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap'))`);
    if (ready) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.ok(ready, 'Dashboard must finish initial render');

  // Focus the sibling-backlog select in Roadmap
  const focused = await cdp.evaluate(`(() => {{
    const sel = document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap[data-row-key="ai-agent-tools:sibling-backlog"]');
    sel.focus();
    window.__sibSelect = sel;
    return document.activeElement === sel;
  }})()`);
  assert.equal(focused, true);

  // Push Wave 2 + quality step 2/3 + sibling task_count change while select holds focus
  await fetch({json.dumps(f"http://127.0.0.1:{ctrl_port}/next")}, {{ method: 'POST' }});
  await cdp.evaluate(`pollDashboard()`);

  const duringFocus = await cdp.evaluate(`(() => {{
    const sec2 = document.getElementById('tier2-execution-epics-wrapper-ai-agent-tools').innerText;
    const sel = document.querySelector('#roadmap-tbody-ai-agent-tools select.select-pic-roadmap[data-row-key="ai-agent-tools:sibling-backlog"]');
    return {{
      sec2,
      sameNode: sel === window.__sibSelect,
      stillFocused: document.activeElement === window.__sibSelect,
    }};
  }})()`);
  assert.equal(duringFocus.sameNode, true, 'Focused select must not be replaced during polling');
  assert.equal(duringFocus.stillFocused, true);
  assert.match(duringFocus.sec2, /Wave 2/, 'Section II must still update live during Roadmap focus');
  assert.match(duringFocus.sec2, /84%/, 'Section II must reflect running 2/3 Gate 4 QA weighted lifecycle progress (84%)');
  assert.match(duringFocus.sec2, /100%/, 'Section II must reflect 4/4 100% task completion');
  assert.match(duringFocus.sec2, /2\/3/, 'Section II must reflect updated quality step 2/3');

  // Change selection on focused select & blur -> must retain selection and apply queued Roadmap update
  await cdp.evaluate(`(() => {{
    const sel = window.__sibSelect;
    sel.value = 'tess';
    sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
    sel.blur();
  }})()`);

  let flushed = null;
  for (let i = 0; i < 30; i++) {{
    flushed = await cdp.evaluate(`(() => {{
      const row = document.querySelector('#roadmap-tbody-ai-agent-tools tr[data-row-key="ai-agent-tools:sibling-backlog"]');
      const sel = row?.querySelector('select.select-pic-roadmap');
      const cells = row?.querySelectorAll('td');
      return {{ pic: sel?.value, taskCount: cells?.[3]?.textContent?.trim() }};
    }})()`);
    if (flushed.pic === 'tess' && flushed.taskCount === '5') break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.equal(flushed.pic, 'tess');
  assert.equal(flushed.taskCount, '5');
  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok', flushed }}));
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
