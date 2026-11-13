"""UI & Chrome CDP integration tests for quota_dashboard.html Modal Stack Controller.

Covers BDD Scenarios:
- RSDH-HP-08: Check-Quota Modal Stack Controller enforces max one inner modal and real iframe reset
- RSDH-EC-07: Check-Quota inner sub-modal backdrop and Escape close only the active inner dialog
- RSDH-ST-06: Check-Quota embedded mode strips redundant outer card frame in real Chrome iframe
- RSDH-FR-05: Pressing Escape with no open inner quota sub-modal closes cleanly via handleCardClose
"""

from __future__ import annotations

import contextlib
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from typing import Any

import pytest  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[1]
QUOTA_DASHBOARD_HTML = (
    REPO_ROOT
    / "skills"
    / "check-quota"
    / "resources"
    / "dashboard"
    / "quota_dashboard.html"
)
CHECK_TASKS_SCRIPT_DIR = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
if str(CHECK_TASKS_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(CHECK_TASKS_SCRIPT_DIR))

import tasks_server  # type: ignore[import-not-found]  # noqa: E402


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


def _run_node_script(script_source: str, timeout: int = 45) -> dict[str, Any]:
    """Execute a Node.js (v25+) verification script and parse its JSON stdout."""
    node_bin = shutil.which("node")
    assert node_bin is not None, "Node.js binary must be installed"

    tmp_path = Path(
        os.path.join(
            os.path.dirname(__file__),
            f".tmp_node_{os.getpid()}_{time.time_ns()}.mjs",
        )
    )
    tmp_path.write_text(script_source, encoding="utf-8")
    try:
        proc = subprocess.run(
            [node_bin, str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    finally:
        tmp_path.unlink(missing_ok=True)

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

const QUOTA_HTML_PATH = __QUOTA_HTML_PATH__;
const html = fs.readFileSync(QUOTA_HTML_PATH, 'utf8');

const scriptMatches = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scriptMatches.length, 1, 'Expected single inline <script> in quota_dashboard.html');
const quotaScript = scriptMatches[0][1];

const bodyMatch = /<body([^>]*)>([\s\S]*?)<script>/.exec(html);
assert.ok(bodyMatch, 'Expected <body> markup in quota_dashboard.html');
const bodyAttrsRaw = bodyMatch[1];
const bodyMarkup = bodyMatch[2];

function createClassList() {
  const classes = new Set();
  return {
    add(...items) { items.forEach((c) => classes.add(c)); },
    remove(...items) { items.forEach((c) => classes.delete(c)); },
    contains(c) { return classes.has(c); },
    toggle(c, force) {
      if (force === true) { classes.add(c); return true; }
      if (force === false) { classes.delete(c); return false; }
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
    this.disabled = false;
    this.checked = false;
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
    if (k === 'value') this.value = String(v);
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
    let stopped = false;
    evt.type = evt.type || 'click';
    evt.target = evt.target || this;
    evt.defaultPrevented = Boolean(evt.defaultPrevented);
    evt.stopPropagation = () => { stopped = true; };
    evt.preventDefault = () => { evt.defaultPrevented = true; };
    let node = this;
    while (node && !stopped) {
      evt.currentTarget = node;
      const fns = node.listeners ? (node.listeners.get(evt.type) || []) : [];
      for (const fn of fns) {
        fn(evt);
      }
      node = node.parentNode || (node === this._doc?.body ? this._doc : null);
    }
    return !evt.defaultPrevented;
  }

  focus() {
    if (this._doc) this._doc.activeElement = this;
  }
  blur() {
    if (this._doc && this._doc.activeElement === this) {
      this._doc.activeElement = this._doc.body;
    }
  }
  contains(node) {
    if (node === this) return true;
    return this.children.some((c) => c.contains(node));
  }

  matches(selector) {
    const parts = String(selector || '').split(',').map((s) => s.trim()).filter(Boolean);
    return parts.some((part) => {
      if (part.startsWith('#')) return this.id === part.slice(1);
      if (part.startsWith('.')) return this.classList.contains(part.slice(1));
      return this.tagName.toLowerCase() === part.toLowerCase();
    });
  }

  closest(selector) {
    let cur = this;
    while (cur && cur.tagName) {
      if (typeof cur.matches === 'function' && cur.matches(selector)) return cur;
      cur = cur.parentNode;
    }
    return null;
  }

  appendChild(child) {
    child.parentNode = this;
    child._doc = this._doc;
    this.children.push(child);
    if (this._doc && child.id) this._doc._byId.set(child.id, child);
    return child;
  }

  remove() {
    if (this.parentNode && Array.isArray(this.parentNode.children)) {
      const idx = this.parentNode.children.indexOf(this);
      if (idx !== -1) this.parentNode.children.splice(idx, 1);
    }
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
    const visit = (node) => {
      for (const ch of node.children) {
        if (ch.matches(selector)) results.push(ch);
        visit(ch);
      }
    };
    visit(this);
    return results;
  }
  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }
}

function createQuotaDomHarness({ search = '', embeddedParent = false } = {}) {
  const storage = new Map();
  const body = new FakeElement('body');
  const doc = {
    _byId: new Map(),
    body,
    documentElement: new FakeElement('html'),
    activeElement: body,
    listeners: new Map(),
    getElementById(id) { return this._byId.get(id) || null; },
    createElement(tag) {
      const el = new FakeElement(tag);
      el._doc = doc;
      return el;
    },
    querySelector(sel) { return body.querySelector(sel); },
    querySelectorAll(sel) { return body.querySelectorAll(sel); },
    addEventListener(type, fn) {
      if (!this.listeners.has(type)) this.listeners.set(type, []);
      this.listeners.get(type).push(fn);
    },
    dispatchEvent(evt) {
      let stopped = false;
      evt.target = evt.target || body;
      evt.defaultPrevented = Boolean(evt.defaultPrevented);
      evt.stopPropagation = () => { stopped = true; };
      evt.preventDefault = () => { evt.defaultPrevented = true; };
      if (!stopped) {
        const fns = this.listeners.get(evt.type) || [];
        for (const fn of fns) fn(evt);
      }
      return !evt.defaultPrevented;
    },
    execCommand() { return true; },
  };
  body._doc = doc;
  const bodyAttrRegex = /([a-zA-Z0-9_-]+)="([^"]*)"/g;
  let bam;
  while ((bam = bodyAttrRegex.exec(bodyAttrsRaw)) !== null) {
    body.setAttribute(bam[1], bam[2]);
  }
  body.innerHTML = bodyMarkup;

  const parentMessages = [];
  let windowClosed = false;
  const winListeners = new Map();

  const windowObj = {
    location: {
      protocol: 'http:',
      origin: 'http://127.0.0.1:8765',
      host: '127.0.0.1:8765',
      search,
    },
    innerWidth: 1280,
    innerHeight: 800,
    close() { windowClosed = true; },
    addEventListener(type, fn) {
      if (!winListeners.has(type)) winListeners.set(type, []);
      winListeners.get(type).push(fn);
    },
    dispatchEvent(evt) {
      const fns = winListeners.get(evt.type) || [];
      for (const fn of fns) fn(evt);
    },
    postMessage(data, _origin) {
      windowObj.dispatchEvent({ type: 'message', data, origin: windowObj.location.origin, source: windowObj });
    },
  };

  const mockParent = {
    postMessage(msg, targetOrigin) {
      parentMessages.push({
        msg: msg === undefined ? undefined : JSON.parse(JSON.stringify(msg)),
        targetOrigin,
      });
    },
  };
  windowObj.parent = embeddedParent ? mockParent : windowObj;

  const sandbox = {
    window: windowObj,
    document: doc,
    localStorage: {
      getItem(k) { return storage.has(k) ? storage.get(k) : null; },
      setItem(k, v) { storage.set(k, String(v)); },
      removeItem(k) { storage.delete(k); },
    },
    navigator: { clipboard: { writeText: async () => {} } },
    fetch: async () => ({ async json() { return { success: false }; } }),
    alert() {},
    confirm() { return true; },
    console: { log() {}, warn() {}, error(...args) { throw new Error('Console error: ' + args.join(' ')); } },
    URLSearchParams,
    URL,
    Event: class Event { constructor(type) { this.type = type; } },
    requestAnimationFrame: (fn) => { if (typeof fn === 'function') fn(); return 0; },
    setTimeout: () => 0,
    clearTimeout: () => {},
    setInterval: () => 0,
    clearInterval: () => {},
  };
  sandbox.globalThis = sandbox;
  sandbox.self = windowObj;

  vm.createContext(sandbox);
  new vm.Script(quotaScript, { filename: 'quota_dashboard.html' }).runInContext(sandbox);
  return {
    sandbox,
    doc,
    windowObj,
    parentMessages,
    isWindowClosed: () => windowClosed,
  };
}
"""


_NODE_CDP_HELPER = r"""
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';

export async function launchHeadlessChromeCdp(chromeBin) {
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'rsdh-quota-cdp-'));
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
    if (msg.method === 'Runtime.executionContextCreated') {
      const ctx = msg.params?.context;
      if (ctx?.auxData?.isDefault && ctx.auxData?.frameId) {
        contextsByFrame.set(ctx.auxData.frameId, ctx.id);
      }
    }
    if (msg.method === 'Runtime.executionContextDestroyed') {
      const ctxId = msg.params?.executionContextId;
      for (const [fid, cid] of contextsByFrame.entries()) {
        if (cid === ctxId) contextsByFrame.delete(fid);
      }
    }
    if (msg.method === 'Runtime.executionContextsCleared') {
      contextsByFrame.clear();
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
      throw new Error(`Evaluation failed: ${JSON.stringify(res.exceptionDetails)}`);
    }
    return res.result?.value;
  }

  async function getQuotaIframeContextId() {
    const tree = await send('Page.getFrameTree');
    const queue = [...(tree.frameTree?.childFrames || [])];
    while (queue.length > 0) {
      const item = queue.shift();
      const fid = item.frame?.id;
      const url = String(item.frame?.url || '');
      if (fid && url.includes('quota_dashboard.html') && contextsByFrame.has(fid)) {
        return contextsByFrame.get(fid);
      }
      if (Array.isArray(item.childFrames)) {
        queue.push(...item.childFrames);
      }
    }
    return null;
  }

  async function waitForQuotaIframeContext(checkExpr, excludeCtxId = null) {
    for (let i = 0; i < 60; i++) {
      const ctx = await getQuotaIframeContextId();
      if (ctx !== null && ctx !== excludeCtxId) {
        try {
          if (await evaluate(checkExpr, ctx)) {
            return ctx;
          }
        } catch (_) {
          // Context may still be transitioning during iframe load
        }
      }
      await new Promise((r) => setTimeout(r, 100));
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
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1280,
    height: 800,
    deviceScaleFactor: 1,
    mobile: false,
  });
  return {
    send,
    evaluate,
    getQuotaIframeContextId,
    waitForQuotaIframeContext,
    clickAt,
    pressEscape,
    close,
    consoleErrors,
    runtimeExceptions,
  };
}
"""


@contextlib.contextmanager
def _start_isolated_quota_and_tasks_servers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Any:
    """Start isolated ephemeral Quota HTTP server + TasksServer serving real HTMLs."""
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

    quota_port = tasks_server.find_available_port(19600)
    quota_http = http.server.ThreadingHTTPServer(
        ("127.0.0.1", quota_port), _QuotaHandler
    )
    threading.Thread(target=quota_http.serve_forever, daemon=True).start()

    # Isolated workspace for real TasksServer + safe /api/launch/quota override
    ws_root = tmp_path / "ws"
    repo_dir = ws_root / "ai-agent-tools"
    (repo_dir / ".devtool").mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, capture_output=True)

    monkeypatch.setattr(
        tasks_server,
        "launch_quota_server",
        lambda workspace_root, port=8765: {
            "status": "ok",
            "action": "mock_ephemeral",
            "url": f"http://127.0.0.1:{quota_port}/quota_dashboard.html",
        },
    )

    tasks_port = tasks_server.find_available_port(19700)
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
            "tasks_url": f"http://127.0.0.1:{srv.server_port}/",
            "quota_url": f"http://127.0.0.1:{quota_port}/quota_dashboard.html",
        }
    finally:
        srv.shutdown()
        srv.server_close()
        quota_http.shutdown()
        quota_http.server_close()


def test_rsdh_hp_08_single_modal_stack_exclusivity() -> None:
    """[RSDH-HP-08] [Tier C - Integration] Node DOM stack controller enforces max one inner modal and postMessage reset."""
    preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
        "__QUOTA_HTML_PATH__", json.dumps(str(QUOTA_DASHBOARD_HTML))
    )
    node_script = (
        preamble
        + r"""
const { sandbox, doc, windowObj } = createQuotaDomHarness({
  search: '?embedded=1&no-auto-refresh=1',
  embeddedParent: true,
});

assert.equal(typeof sandbox.openInnerModal, 'function', 'openInnerModal must be defined');
assert.equal(typeof sandbox.closeInnerModal, 'function', 'closeInnerModal must be defined');
assert.equal(typeof sandbox.closeAllInnerModals, 'function', 'closeAllInnerModals must be defined');
assert.equal(typeof sandbox.getActiveInnerModal, 'function', 'getActiveInnerModal must be defined');

const modalIds = ['scheduleModal', 'loginModal', 'profileInfoModal', 'appealDetailModal'];
const openModalIds = () => modalIds.filter((id) => !doc.getElementById(id).classList.contains('hidden'));

assert.deepEqual(openModalIds(), [], 'All inner modals start closed');
assert.equal(sandbox.getActiveInnerModal(), null);

// Open scheduleModal -> then open loginModal -> scheduleModal must auto-close
sandbox.openScheduleModal('brother');
assert.deepEqual(openModalIds(), ['scheduleModal']);
assert.equal(sandbox.getActiveInnerModal(), 'scheduleModal');

sandbox.openLoginModal('brother');
assert.deepEqual(openModalIds(), ['loginModal'], 'Opening loginModal must auto-close scheduleModal');
assert.equal(sandbox.getActiveInnerModal(), 'loginModal');

sandbox.openProfileInfoModal('brother');
assert.deepEqual(openModalIds(), ['profileInfoModal'], 'Opening profileInfoModal must auto-close loginModal');
assert.equal(sandbox.getActiveInnerModal(), 'profileInfoModal');

sandbox.openAppealModal('brother');
assert.deepEqual(openModalIds(), ['appealDetailModal'], 'Opening appealDetailModal must auto-close profileInfoModal');
assert.equal(sandbox.getActiveInnerModal(), 'appealDetailModal');

// Untrusted remote origin reset message must be ignored
windowObj.dispatchEvent({
  type: 'message',
  origin: 'https://untrusted.example.com',
  data: { action: 'reset_quota_submodals' },
});
assert.deepEqual(openModalIds(), ['appealDetailModal'], 'Untrusted origin message must be ignored');

// Trusted parent reset_quota_submodals must close all inner modals
windowObj.dispatchEvent({
  type: 'message',
  origin: 'http://127.0.0.1:8766',
  data: { action: 'reset_quota_submodals' },
});
assert.deepEqual(openModalIds(), [], 'reset_quota_submodals must close all inner modals');
assert.equal(sandbox.getActiveInnerModal(), null);

// Verify Design Spec §4.7 aliases & unknown modal guard
assert.equal(sandbox.openInnerModal('nonexistentModal'), false);
assert.equal(sandbox.openQuotaSubModal('profileInfoModal'), true);
assert.deepEqual(openModalIds(), ['profileInfoModal']);
assert.equal(sandbox.openQuotaSubModal('loginModal'), true);
assert.deepEqual(openModalIds(), ['loginModal']);
sandbox.closeAllQuotaSubModals();
assert.deepEqual(openModalIds(), []);

console.log(JSON.stringify({ status: 'ok' }));
"""
    )
    node_res = _run_node_script(node_script)
    assert node_res["status"] == "ok"


class TestQuotaModalStack_Integration:
    """Integration runner suite verifying real Chrome CDP and live server DOM behavior."""

    def test_rsdh_hp_08_chrome_cdp_integration(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """[RSDH-HP-08] [Tier C - Integration] Check-Quota Modal Stack Controller enforces max one inner modal and real iframe reset."""
        chrome_bin = _resolve_chrome_binary()
        cdp_helper_path = tmp_path / "cdp_helper.mjs"
        cdp_helper_path.write_text(_NODE_CDP_HELPER, encoding="utf-8")

        with _start_isolated_quota_and_tasks_servers(tmp_path, monkeypatch) as urls:
            cdp_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(cdp_helper_path))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Page.navigate', {{ url: {json.dumps(urls["tasks_url"])} }});
  let tasksReady = false;
  for (let i = 0; i < 40; i++) {{
    tasksReady = await cdp.evaluate(`typeof openQuotaModal === 'function'`);
    if (tasksReady) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  assert.ok(tasksReady, 'tasks_dashboard.html must initialize');

  await cdp.evaluate(`openQuotaModal()`);
  const iframeCtx = await cdp.waitForQuotaIframeContext(
    `typeof getActiveInnerModal === 'function' && typeof openScheduleModal === 'function'`,
  );
  assert.ok(iframeCtx !== null, 'Quota iframe must load inside #modal-quota');

  const getOpenIdsExpr = `['scheduleModal', 'loginModal', 'profileInfoModal', 'appealDetailModal'].filter(id => !document.getElementById(id).classList.contains('hidden'))`;

  await cdp.evaluate(`openScheduleModal('brother')`, iframeCtx);
  let openIds = await cdp.evaluate(getOpenIdsExpr, iframeCtx);
  assert.deepEqual(openIds, ['scheduleModal']);

  await cdp.evaluate(`openLoginModal('brother')`, iframeCtx);
  openIds = await cdp.evaluate(getOpenIdsExpr, iframeCtx);
  assert.deepEqual(openIds, ['loginModal'], 'Chrome CDP: opening #loginModal must auto-close #scheduleModal');

  // Close parent #modal-quota -> posts reset_quota_submodals across real iframe boundary
  await cdp.evaluate(`closeLiveModal('modal-quota')`);
  for (let i = 0; i < 30; i++) {{
    openIds = await cdp.evaluate(getOpenIdsExpr, iframeCtx);
    if (openIds.length === 0) break;
    await new Promise((r) => setTimeout(r, 50));
  }}
  assert.deepEqual(openIds, [], 'Closing #modal-quota must reset all inner quota sub-modals via postMessage');

  // Reopen #modal-quota -> wait for reloaded iframe context and confirm zero stale inner sub-modals
  await cdp.evaluate(`openQuotaModal()`);
  const reopenedCtx = await cdp.waitForQuotaIframeContext(
    `typeof getActiveInnerModal === 'function'`,
    iframeCtx,
  );
  assert.ok(reopenedCtx !== null, 'Reopened quota iframe must be ready');
  const reopenedOpenIds = await cdp.evaluate(getOpenIdsExpr, reopenedCtx);
  assert.deepEqual(reopenedOpenIds, [], 'Reopening #modal-quota must reveal zero stale inner sub-modals');

  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok', openIds }}));
}} finally {{
  await cdp.close();
}}
"""
            cdp_res = _run_node_script(cdp_script, timeout=60)
            assert cdp_res["status"] == "ok"

    def test_rsdh_ec_07_inner_modal_backdrop_and_escape(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """[RSDH-EC-07] [Tier C - Integration] Check-Quota inner sub-modal backdrop and Escape close only the active inner dialog."""
        # Part A: Node DOM checks for all 4 inner modals (backdrop click, inner card click, Escape)
        preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
            "__QUOTA_HTML_PATH__", json.dumps(str(QUOTA_DASHBOARD_HTML))
        )
        node_script = (
            preamble
            + r"""
const { sandbox, doc, parentMessages } = createQuotaDomHarness({
  search: '?embedded=1&no-auto-refresh=1',
  embeddedParent: true,
});

const cases = [
  ['scheduleModal', () => sandbox.openScheduleModal('brother')],
  ['loginModal', () => sandbox.openLoginModal('brother')],
  ['profileInfoModal', () => sandbox.openProfileInfoModal('brother')],
  ['appealDetailModal', () => sandbox.openAppealModal('brother')],
];

for (const [modalId, opener] of cases) {
  opener();
  const modalEl = doc.getElementById(modalId);
  const innerCard = modalEl.firstElementChild;
  assert.ok(innerCard, `${modalId} must have inner card child`);
  assert.equal(modalEl.classList.contains('hidden'), false, `${modalId} must open`);

  // Clicking inside inner dialog card must NOT close inner modal or parent #modal-quota
  innerCard.dispatchEvent({ type: 'click', target: innerCard });
  assert.equal(modalEl.classList.contains('hidden'), false, `${modalId} must remain open when clicking inside dialog card`);
  assert.equal(parentMessages.length, 0, `Clicking inside ${modalId} must not post close_quota_modal`);

  // Clicking inner modal backdrop (e.target === modalEl) closes ONLY that inner modal
  modalEl.dispatchEvent({ type: 'click', target: modalEl });
  assert.equal(modalEl.classList.contains('hidden'), true, `${modalId} backdrop click must close ${modalId}`);
  assert.equal(sandbox.getActiveInnerModal(), null);
  assert.equal(parentMessages.length, 0, `${modalId} backdrop click must NOT close parent #modal-quota`);

  // Re-open and press Escape -> closes ONLY that inner modal with preventDefault + stopPropagation
  opener();
  const escEvt = { type: 'keydown', key: 'Escape' };
  const notPrevented = doc.dispatchEvent(escEvt);
  assert.equal(notPrevented, false, `Escape on ${modalId} must call preventDefault()`);
  assert.equal(modalEl.classList.contains('hidden'), true, `Escape must close ${modalId}`);
  assert.equal(sandbox.getActiveInnerModal(), null);
  assert.equal(parentMessages.length, 0, `Escape on ${modalId} must NOT invoke handleCardClose()`);
}

// Clicking outside #dashboardCard on body while 0 inner modals are open closes parent #modal-quota
doc.body.dispatchEvent({ type: 'click', target: doc.body });
assert.equal(parentMessages.length, 1);
assert.deepEqual(parentMessages[0].msg, { action: 'close_quota_modal' });

console.log(JSON.stringify({ status: 'ok', checkedModals: cases.map((c) => c[0]) }));
"""
        )
        node_res = _run_node_script(node_script)
        assert node_res["status"] == "ok"

        # Part B: Real Chrome CDP mouse click on backdrop + real keyboard Escape inside iframe
        chrome_bin = _resolve_chrome_binary()
        cdp_helper_path = tmp_path / "cdp_helper.mjs"
        cdp_helper_path.write_text(_NODE_CDP_HELPER, encoding="utf-8")

        with _start_isolated_quota_and_tasks_servers(tmp_path, monkeypatch) as urls:
            cdp_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(cdp_helper_path))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Page.navigate', {{ url: {json.dumps(urls["tasks_url"])} }});
  for (let i = 0; i < 40; i++) {{
    if (await cdp.evaluate(`typeof openQuotaModal === 'function'`)) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  await cdp.evaluate(`openQuotaModal()`);
  const iframeCtx = await cdp.waitForQuotaIframeContext(`typeof getActiveInnerModal === 'function'`);
  assert.ok(iframeCtx !== null, 'Quota iframe context must be ready');

  const rect = await cdp.evaluate(`(() => {{
    const r = document.getElementById('quota-iframe').getBoundingClientRect();
    return {{ left: r.left, top: r.top }};
  }})()`);

  // 1. Backdrop click on all 4 modals keeps #modal-quota open
  for (const [modalId, openCall] of [
    ['profileInfoModal', "openProfileInfoModal('brother')"],
    ['appealDetailModal', "openAppealModal('brother')"],
    ['scheduleModal', "openScheduleModal('brother')"],
    ['loginModal', "openLoginModal('brother')"],
  ]) {{
    await cdp.evaluate(openCall, iframeCtx);
    const active = await cdp.evaluate(`getActiveInnerModal()`, iframeCtx);
    assert.equal(active, modalId);

    const hitId = await cdp.evaluate(`document.elementFromPoint(12, 12)?.id`, iframeCtx);
    assert.equal(hitId, modalId, `Top-left corner must hit ${{modalId}} backdrop`);

    await cdp.clickAt(rect.left + 12, rect.top + 12);
    const afterClick = await cdp.evaluate(`({{
      innerHidden: document.getElementById(${{JSON.stringify(modalId)}}).classList.contains('hidden'),
      active: getActiveInnerModal(),
    }})`, iframeCtx);
    assert.equal(afterClick.innerHidden, true, `${{modalId}} must close on backdrop click`);
    assert.equal(afterClick.active, null);

    const parentDisplay = await cdp.evaluate(`getComputedStyle(document.getElementById('modal-quota')).display`);
    assert.equal(parentDisplay, 'flex', `#modal-quota must remain open after ${{modalId}} backdrop click`);
  }}

  // 2. Real Escape key dismisses active inner modal while keeping #modal-quota open
  for (const [modalId, openCall] of [
    ['profileInfoModal', "openProfileInfoModal('brother')"],
    ['scheduleModal', "openScheduleModal('brother')"],
  ]) {{
    await cdp.evaluate(openCall, iframeCtx);
    // Click inside inner card so Chrome routes keyboard focus directly to the iframe
    const cardPt = await cdp.evaluate(`(() => {{
      const card = document.getElementById(${{JSON.stringify(modalId)}}).firstElementChild;
      const r = card.getBoundingClientRect();
      return {{ x: r.left + r.width / 2, y: r.top + 20 }};
    }})()`, iframeCtx);
    await cdp.clickAt(rect.left + cardPt.x, rect.top + cardPt.y);

    await cdp.pressEscape();
    await new Promise((r) => setTimeout(r, 80));

    const afterEsc = await cdp.evaluate(`({{
      innerHidden: document.getElementById(${{JSON.stringify(modalId)}}).classList.contains('hidden'),
      active: getActiveInnerModal(),
    }})`, iframeCtx);
    assert.equal(afterEsc.innerHidden, true, `Escape must close ${{modalId}}`);
    assert.equal(afterEsc.active, null);

    const parentDisplay = await cdp.evaluate(`getComputedStyle(document.getElementById('modal-quota')).display`);
    assert.equal(parentDisplay, 'flex', `#modal-quota must stay open after Escape closed ${{modalId}}`);
  }}

  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok' }}));
}} finally {{
  await cdp.close();
}}
"""
            cdp_res = _run_node_script(cdp_script, timeout=60)
            assert cdp_res["status"] == "ok"

    def test_rsdh_st_06_embedded_mode_flattens_card(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """[RSDH-ST-06] [Tier C - Integration] Check-Quota embedded mode strips redundant outer card frame in real Chrome iframe."""
        # Part A: Node DOM verification of ?embedded=1 and window.parent !== window fallback detection
        preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
            "__QUOTA_HTML_PATH__", json.dumps(str(QUOTA_DASHBOARD_HTML))
        )
        node_script = (
            preamble
            + r"""
const standalone = createQuotaDomHarness({ search: '?no-auto-refresh=1', embeddedParent: false });
assert.equal(standalone.doc.body.classList.contains('embedded-mode'), false);
assert.equal(standalone.doc.getElementById('dashboardCard').classList.contains('embedded-mode'), false);

const queryEmbedded = createQuotaDomHarness({ search: '?embedded=1&no-auto-refresh=1', embeddedParent: false });
assert.equal(queryEmbedded.doc.body.classList.contains('embedded-mode'), true);
assert.equal(queryEmbedded.doc.getElementById('dashboardCard').classList.contains('embedded-mode'), true);

const iframeFallback = createQuotaDomHarness({ search: '?no-auto-refresh=1', embeddedParent: true });
assert.equal(iframeFallback.doc.body.classList.contains('embedded-mode'), true);
assert.equal(iframeFallback.doc.getElementById('dashboardCard').classList.contains('embedded-mode'), true);

console.log(JSON.stringify({ status: 'ok' }));
"""
        )
        node_res = _run_node_script(node_script)
        assert node_res["status"] == "ok"

        # Part B: Real Chrome CDP comparing computed styles of #dashboardCard standalone vs real iframe ?embedded=1
        chrome_bin = _resolve_chrome_binary()
        cdp_helper_path = tmp_path / "cdp_helper.mjs"
        cdp_helper_path.write_text(_NODE_CDP_HELPER, encoding="utf-8")

        with _start_isolated_quota_and_tasks_servers(tmp_path, monkeypatch) as urls:
            style_expr = r"""(() => {
              const card = document.getElementById('dashboardCard');
              const cs = window.getComputedStyle(card);
              const bs = window.getComputedStyle(document.body);
              return {
                hasEmbeddedClass: card.classList.contains('embedded-mode') && document.body.classList.contains('embedded-mode'),
                borderTopWidth: cs.borderTopWidth,
                borderTopStyle: cs.borderTopStyle,
                borderRadius: cs.borderRadius,
                boxShadow: cs.boxShadow,
                paddingTop: cs.paddingTop,
                paddingLeft: cs.paddingLeft,
                marginLeft: cs.marginLeft,
                marginRight: cs.marginRight,
                bodyPaddingTop: bs.paddingTop,
              };
            })()"""
            cdp_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(cdp_helper_path))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  // 1. Standalone view
  await cdp.send('Page.navigate', {{ url: {json.dumps(urls["quota_url"])} }});
  for (let i = 0; i < 40; i++) {{
    if (await cdp.evaluate(`Boolean(document.getElementById('dashboardCard'))`)) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  const standalone = await cdp.evaluate({json.dumps(style_expr)});
  assert.equal(standalone.hasEmbeddedClass, false, 'Standalone mode must not set embedded-mode class');
  assert.equal(standalone.borderTopWidth, '1px', 'Standalone card must preserve 1px border');
  assert.equal(standalone.borderTopStyle, 'solid', 'Standalone card must preserve solid border');
  assert.notEqual(standalone.boxShadow, 'none', 'Standalone card must preserve box-shadow');
  assert.ok(parseFloat(standalone.borderRadius) > 0, 'Standalone card must preserve rounded corners');
  assert.ok(parseFloat(standalone.paddingTop) >= 16, 'Standalone card must preserve card padding');

  // 2. Embedded ?embedded=1 inside #modal-quota real iframe
  await cdp.send('Page.navigate', {{ url: {json.dumps(urls["tasks_url"])} }});
  for (let i = 0; i < 40; i++) {{
    if (await cdp.evaluate(`typeof openQuotaModal === 'function'`)) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  await cdp.evaluate(`openQuotaModal()`);
  const iframeCtx = await cdp.waitForQuotaIframeContext(`Boolean(document.getElementById('dashboardCard'))`);
  assert.ok(iframeCtx !== null, 'Embedded quota iframe must mount');

  const embedded = await cdp.evaluate({json.dumps(style_expr)}, iframeCtx);
  assert.equal(embedded.hasEmbeddedClass, true, 'Embedded mode must apply embedded-mode class');
  assert.equal(embedded.borderTopWidth, '0px', 'Embedded mode must strip outer card border');
  assert.equal(embedded.boxShadow, 'none', 'Embedded mode must strip outer card shadow');
  assert.equal(embedded.borderRadius, '0px', 'Embedded mode must flatten border-radius');
  assert.equal(embedded.marginLeft, '0px', 'Embedded mode must flatten horizontal margin');
  assert.equal(embedded.bodyPaddingTop, '0px', 'Embedded mode must strip outer body padding');
  assert.ok(
    parseFloat(embedded.paddingTop) < parseFloat(standalone.paddingTop),
    `Embedded card padding (${{embedded.paddingTop}}) must be strictly less than standalone (${{standalone.paddingTop}})`,
  );

  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok', standalone, embedded }}));
}} finally {{
  await cdp.close();
}}
"""
            cdp_res = _run_node_script(cdp_script, timeout=60)
            assert cdp_res["status"] == "ok"

    def test_rsdh_fr_05_escape_with_zero_inner_modals_closes_card(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """[RSDH-FR-05] [Tier C - Integration] Pressing Escape with no open inner quota sub-modal closes cleanly via handleCardClose."""
        # Part A: Node DOM checks (embedded postMessage + standalone window.close)
        preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
            "__QUOTA_HTML_PATH__", json.dumps(str(QUOTA_DASHBOARD_HTML))
        )
        node_script = (
            preamble
            + r"""
const embedded = createQuotaDomHarness({ search: '?embedded=1&no-auto-refresh=1', embeddedParent: true });
assert.equal(embedded.sandbox.getActiveInnerModal(), null);
embedded.doc.dispatchEvent({ type: 'keydown', key: 'Escape' });
assert.equal(embedded.parentMessages.length, 1);
assert.deepEqual(embedded.parentMessages[0].msg, { action: 'close_quota_modal' });

const standalone = createQuotaDomHarness({ search: '?no-auto-refresh=1', embeddedParent: false });
assert.equal(standalone.sandbox.getActiveInnerModal(), null);
standalone.doc.dispatchEvent({ type: 'keydown', key: 'Escape' });
assert.equal(standalone.isWindowClosed(), true);

console.log(JSON.stringify({ status: 'ok' }));
"""
        )
        node_res = _run_node_script(node_script)
        assert node_res["status"] == "ok"

        # Part B: Real Chrome CDP Escape cascade inside #modal-quota iframe when 0 inner modals are open
        chrome_bin = _resolve_chrome_binary()
        cdp_helper_path = tmp_path / "cdp_helper.mjs"
        cdp_helper_path.write_text(_NODE_CDP_HELPER, encoding="utf-8")

        with _start_isolated_quota_and_tasks_servers(tmp_path, monkeypatch) as urls:
            cdp_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(cdp_helper_path))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Page.navigate', {{ url: {json.dumps(urls["tasks_url"])} }});
  for (let i = 0; i < 40; i++) {{
    if (await cdp.evaluate(`typeof openQuotaModal === 'function'`)) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  await cdp.evaluate(`openQuotaModal()`);
  const iframeCtx = await cdp.waitForQuotaIframeContext(`typeof getActiveInnerModal === 'function'`);
  assert.ok(iframeCtx !== null);

  assert.equal(await cdp.evaluate(`getActiveInnerModal()`, iframeCtx), null);

  // Focus inside iframe by clicking dashboard header title
  const hdrPt = await cdp.evaluate(`(() => {{
    const r = document.getElementById('dashboardHeader').getBoundingClientRect();
    return {{ x: r.left + 40, y: r.top + 20 }};
  }})()`, iframeCtx);
  const iframeRect = await cdp.evaluate(`(() => {{
    const r = document.getElementById('quota-iframe').getBoundingClientRect();
    return {{ left: r.left, top: r.top }};
  }})()`);
  await cdp.clickAt(iframeRect.left + hdrPt.x, iframeRect.top + hdrPt.y);

  // Press Escape with 0 inner modals open -> handleCardClose() posts close_quota_modal to parent
  await cdp.pressEscape();

  let modalClosed = false;
  for (let i = 0; i < 30; i++) {{
    const disp = await cdp.evaluate(`getComputedStyle(document.getElementById('modal-quota')).display`);
    if (disp === 'none') {{
      modalClosed = true;
      break;
    }}
    await new Promise((r) => setTimeout(r, 50));
  }}
  assert.equal(modalClosed, true, 'Escape with 0 open inner sub-modals must close #modal-quota cleanly');

  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok', modalClosed }}));
}} finally {{
  await cdp.close();
}}
"""
            cdp_res = _run_node_script(cdp_script, timeout=60)
            assert cdp_res["status"] == "ok"

    def test_batch_schedule_toggle_keeps_embedded_quota_modal_open(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """[Regression] Clicking 'Lên lịch nhiều tài khoản' or 'Thoát chọn' must not close embedded #modal-quota."""
        # Part A: Node DOM check for detached child target after toggleBatchSelectMode()
        preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
            "__QUOTA_HTML_PATH__", json.dumps(str(QUOTA_DASHBOARD_HTML))
        )
        node_script = (
            preamble
            + r"""
const { sandbox, doc, parentMessages } = createQuotaDomHarness({
  search: '?embedded=1&no-auto-refresh=1',
  embeddedParent: true,
});

const batchBtn = doc.getElementById('batchScheduleBtn');
assert.ok(batchBtn, 'batchScheduleBtn must exist');
const initialLabelSpan = batchBtn.children[batchBtn.children.length - 1];
assert.ok(initialLabelSpan, 'batchScheduleBtn must have span child');

// Emulate real click bubbling: onclick runs toggleBatchSelectMode() on btn, then event reaches document
batchBtn.addEventListener('click', () => sandbox.toggleBatchSelectMode());
initialLabelSpan.dispatchEvent({ type: 'click', target: initialLabelSpan });

assert.equal(
  doc.getElementById('batchBottomBar').classList.contains('hidden'),
  false,
  'Clicking Lên lịch nhiều tài khoản must open batchBottomBar',
);
assert.equal(
  parentMessages.length,
  0,
  'Clicking child span inside batchScheduleBtn must NOT post close_quota_modal',
);

const exitLabelSpan = batchBtn.children[batchBtn.children.length - 1];
exitLabelSpan.dispatchEvent({ type: 'click', target: exitLabelSpan });
assert.equal(
  doc.getElementById('batchBottomBar').classList.contains('hidden'),
  true,
  'Clicking Thoát chọn must close batchBottomBar',
);
assert.equal(
  parentMessages.length,
  0,
  'Clicking Thoát chọn must NOT post close_quota_modal',
);

// Simulated grid child re-render (e.g. checkbox toggle calling renderAllProfiles)
const col1 = doc.getElementById('gridCol1');
assert.ok(col1, 'gridCol1 must exist');
const cardTarget = doc.createElement('span');
col1.appendChild(cardTarget);
col1.addEventListener('click', () => sandbox.renderAllProfiles());
cardTarget.dispatchEvent({ type: 'click', target: cardTarget });
assert.equal(
  doc.body.contains(cardTarget),
  false,
  'renderAllProfiles() must detach cardTarget from gridCol1',
);
assert.equal(
  parentMessages.length,
  0,
  'Detached target from inside dashboardCard must NOT post close_quota_modal',
);

// Genuine click outside #dashboardCard still closes #modal-quota
doc.body.dispatchEvent({ type: 'click', target: doc.body });
assert.equal(parentMessages.length, 1);
assert.deepEqual(parentMessages[0].msg, { action: 'close_quota_modal' });

console.log(JSON.stringify({ status: 'ok' }));
"""
        )
        node_res = _run_node_script(node_script)
        assert node_res["status"] == "ok"

        # Part B: Real Chrome CDP click coordinates on child <span> of #batchScheduleBtn inside #modal-quota iframe
        chrome_bin = _resolve_chrome_binary()
        cdp_helper_path = tmp_path / "cdp_helper.mjs"
        cdp_helper_path.write_text(_NODE_CDP_HELPER, encoding="utf-8")

        with _start_isolated_quota_and_tasks_servers(tmp_path, monkeypatch) as urls:
            cdp_script = rf"""
import assert from 'node:assert/strict';
import {{ launchHeadlessChromeCdp }} from {json.dumps(str(cdp_helper_path))};

const cdp = await launchHeadlessChromeCdp({json.dumps(chrome_bin)});
try {{
  await cdp.send('Page.navigate', {{ url: {json.dumps(urls["tasks_url"])} }});
  for (let i = 0; i < 40; i++) {{
    if (await cdp.evaluate(`typeof openQuotaModal === 'function'`)) break;
    await new Promise((r) => setTimeout(r, 100));
  }}
  await cdp.evaluate(`openQuotaModal()`);
  const iframeCtx = await cdp.waitForQuotaIframeContext(`typeof toggleBatchSelectMode === 'function'`);
  assert.ok(iframeCtx !== null, 'Quota iframe context must be ready');

  const iframeRect = await cdp.evaluate(`(() => {{
    const r = document.getElementById('quota-iframe').getBoundingClientRect();
    return {{ left: r.left, top: r.top }};
  }})()`);

  async function clickSpanInsideBatchBtn() {{
    const pt = await cdp.evaluate(`(() => {{
      const span = document.querySelector('#batchScheduleBtn span:last-child');
      const r = span.getBoundingClientRect();
      return {{ x: r.left + r.width / 2, y: r.top + r.height / 2, text: span.textContent.trim() }};
    }})()`, iframeCtx);
    await cdp.clickAt(iframeRect.left + pt.x, iframeRect.top + pt.y);
    await new Promise((r) => setTimeout(r, 80));
    return pt.text;
  }}

  // 1. Click "Lên lịch nhiều tài khoản" child <span> -> opens bottom bar & keeps #modal-quota open
  const enterText = await clickSpanInsideBatchBtn();
  assert.equal(enterText, 'Lên lịch nhiều tài khoản');
  assert.equal(
    await cdp.evaluate(`getComputedStyle(document.getElementById('modal-quota')).display`),
    'flex',
    '#modal-quota must remain open after clicking Lên lịch nhiều tài khoản',
  );
  assert.equal(
    await cdp.evaluate(`document.getElementById('batchBottomBar').classList.contains('hidden')`, iframeCtx),
    false,
    'batchBottomBar must be visible',
  );

  // 2. Click "Chọn tất cả" -> renderAllProfiles() must keep #modal-quota open
  const selectAllPt = await cdp.evaluate(`(() => {{
    const btn = document.querySelector('#batchBottomBar button[onclick*="selectAllProfiles(true)"]');
    const r = btn.getBoundingClientRect();
    return {{ x: r.left + r.width / 2, y: r.top + r.height / 2 }};
  }})()`, iframeCtx);
  await cdp.clickAt(iframeRect.left + selectAllPt.x, iframeRect.top + selectAllPt.y);
  await new Promise((r) => setTimeout(r, 80));
  assert.equal(
    await cdp.evaluate(`getComputedStyle(document.getElementById('modal-quota')).display`),
    'flex',
    '#modal-quota must stay open after Chọn tất cả re-render',
  );

  // 3. Click "Thoát chọn" child <span> -> exits batch mode & keeps #modal-quota open
  const exitText = await clickSpanInsideBatchBtn();
  assert.equal(exitText, 'Thoát chọn');
  assert.equal(
    await cdp.evaluate(`getComputedStyle(document.getElementById('modal-quota')).display`),
    'flex',
    '#modal-quota must remain open after clicking Thoát chọn',
  );
  assert.equal(
    await cdp.evaluate(`document.getElementById('batchBottomBar').classList.contains('hidden')`, iframeCtx),
    true,
    'batchBottomBar must hide after Thoát chọn',
  );

  // 4. Toggle batch mode again and click "Hủy" button -> keeps #modal-quota open
  await clickSpanInsideBatchBtn();
  const cancelPt = await cdp.evaluate(`(() => {{
    const btn = document.querySelector('#batchBottomBar button[onclick*="exitBatchSelectMode"]');
    const r = btn.getBoundingClientRect();
    return {{ x: r.left + r.width / 2, y: r.top + r.height / 2 }};
  }})()`, iframeCtx);
  await cdp.clickAt(iframeRect.left + cancelPt.x, iframeRect.top + cancelPt.y);
  await new Promise((r) => setTimeout(r, 80));
  assert.equal(
    await cdp.evaluate(`getComputedStyle(document.getElementById('modal-quota')).display`),
    'flex',
    '#modal-quota must remain open after clicking Hủy',
  );

  assert.deepEqual(cdp.consoleErrors, [], `Unexpected console errors: ${{cdp.consoleErrors}}`);
  assert.deepEqual(cdp.runtimeExceptions, [], `Unexpected runtime exceptions: ${{cdp.runtimeExceptions}}`);
  console.log(JSON.stringify({{ status: 'ok' }}));
}} finally {{
  await cdp.close();
}}
"""
            cdp_res = _run_node_script(cdp_script, timeout=60)
            assert cdp_res["status"] == "ok"
