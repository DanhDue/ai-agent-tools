"""End-to-end and unit acceptance suite for Task 05 review action extraction and UI.

Covers:
- CQRA-HP-05: Cross-Model Review parser + tasks_dashboard.html headless Chrome CDP E2E
- CQRA-EC-03: Multi-prefix Problem extraction, 6-col header mapping, and fix_plan variants
- CQRA-ST-03: Unconditional watch_paths cache invalidation on fix_plan creation and edit
- CQRA-FR-03: Malformed fix_plan_roundN.md fault resilience across HTTP endpoints
"""

from __future__ import annotations

import base64
from collections.abc import Iterator
import contextlib
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
from typing import Any
import urllib.parse
import urllib.request

import pytest  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_SCRIPTS_DIR = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
if str(TASKS_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(TASKS_SCRIPTS_DIR))

import tasks_server  # type: ignore[import-not-found]  # noqa: E402


def _pick_free_port() -> int:
    """Ask the OS kernel for an ephemeral localhost TCP port, then verify via find_available_port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        ephemeral = int(sock.getsockname()[1])
    return tasks_server.find_available_port(ephemeral)


def _find_chrome_binary() -> str:
    """Locate Google Chrome / Chromium binary for headless CDP verification."""
    candidates = [
        os.environ.get("CHROME_BIN", ""),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome") or "",
        shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "",
    ]
    for cand in candidates:
        if cand and Path(cand).is_file():
            return cand
    raise RuntimeError("Headless Chrome binary not found on host for Tier C CDP E2E.")


class _CdpSession:
    """Minimal stdlib RFC 6455 WebSocket Chrome DevTools Protocol client."""

    def __init__(self, ws_url: str, timeout: float = 10.0) -> None:
        parsed = urllib.parse.urlparse(ws_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 80
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        self._sock = socket.create_connection((host, port), timeout=timeout)
        self._buf = bytearray()
        self._next_id = 0
        self.console_errors: list[str] = []
        self.uncaught_exceptions: list[str] = []

        ws_key = base64.b64encode(os.urandom(16)).decode("ascii")
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {ws_key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode("ascii")
        self._sock.sendall(handshake)

        header_buf = bytearray()
        while b"\r\n\r\n" not in header_buf:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("CDP WebSocket handshake closed prematurely")
            header_buf.extend(chunk)
        sep_idx = header_buf.index(b"\r\n\r\n") + 4
        status_line = header_buf[:sep_idx].splitlines()[0].decode("latin1")
        if "101" not in status_line:
            raise ConnectionError(f"CDP WebSocket upgrade failed: {status_line}")
        if sep_idx < len(header_buf):
            self._buf.extend(header_buf[sep_idx:])

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass

    def _read_exact(self, n: int) -> bytes:
        while len(self._buf) < n:
            chunk = self._sock.recv(max(4096, n - len(self._buf)))
            if not chunk:
                raise ConnectionError("CDP WebSocket closed while reading frame")
            self._buf.extend(chunk)
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        mask_key = os.urandom(4)
        length = len(payload)
        header = bytearray([0x80 | (opcode & 0x0F)])
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.extend(struct.pack("!BH", 0x80 | 126, length))
        else:
            header.extend(struct.pack("!BQ", 0x80 | 127, length))
        masked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        self._sock.sendall(bytes(header) + mask_key + masked)

    def _recv_message(self) -> str:
        fragments: list[bytes] = []
        while True:
            b0, b1 = self._read_exact(2)
            fin = bool(b0 & 0x80)
            opcode = b0 & 0x0F
            masked = bool(b1 & 0x80)
            length = b1 & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._read_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._read_exact(8))[0]
            mask_key = self._read_exact(4) if masked else b""
            payload = self._read_exact(length)
            if masked:
                payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))

            if opcode == 0x8:
                raise ConnectionError("CDP WebSocket closed by peer")
            if opcode == 0x9:
                self._send_frame(0xA, payload)
                continue
            if opcode == 0xA:
                continue
            fragments.append(payload)
            if fin:
                return b"".join(fragments).decode("utf-8", errors="replace")

    def _record_event(self, msg: dict[str, Any]) -> None:
        method = msg.get("method")
        params = msg.get("params") or {}
        if method == "Runtime.exceptionThrown":
            details = params.get("exceptionDetails") or {}
            text = str(details.get("text") or "Uncaught exception")
            exc_obj = details.get("exception") or {}
            desc = str(exc_obj.get("description") or "")
            self.uncaught_exceptions.append(f"{text}: {desc}".strip(": "))
        elif method == "Runtime.consoleAPICalled":
            if params.get("type") == "error":
                args = params.get("args") or []
                rendered = " ".join(
                    str(a.get("value") or a.get("description") or "") for a in args
                ).strip()
                self.console_errors.append(rendered or "console.error")

    def call(
        self, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self._next_id += 1
        req_id = self._next_id
        body = json.dumps(
            {"id": req_id, "method": method, "params": params or {}}
        ).encode("utf-8")
        self._send_frame(0x1, body)
        while True:
            raw = self._recv_message()
            msg: dict[str, Any] = json.loads(raw)
            if "method" in msg:
                self._record_event(msg)
                continue
            if msg.get("id") == req_id:
                if "error" in msg:
                    raise RuntimeError(f"CDP {method} error: {msg['error']}")
                res: dict[str, Any] = msg.get("result") or {}
                return res

    def eval_js(self, expression: str, await_promise: bool = True) -> Any:
        res = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise,
            },
        )
        if "exceptionDetails" in res:
            self._record_event(
                {
                    "method": "Runtime.exceptionThrown",
                    "params": {"exceptionDetails": res["exceptionDetails"]},
                }
            )
            raise RuntimeError(f"JS evaluation threw: {res['exceptionDetails']}")
        remote_obj = res.get("result") or {}
        return remote_obj.get("value")


def _write_epic_hld(epic_dir: Path, slug: str) -> None:
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / f"{slug}.en.md").write_text(
        f"# Epic {slug}\n\n"
        "## Meta Data\n\n"
        f"- **Epic name**: `{slug}`\n"
        "- **Status**: In Progress\n"
        "- **PIC**: `nguyenhieu000690`\n",
        encoding="utf-8",
    )


@pytest.fixture(scope="module")
def tasks_e2e_workspace(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, Any]]:
    """Module-scoped temporary workspace + live TasksServer bound to an isolated port & pid file."""
    ws_root = tmp_path_factory.mktemp("cqra_tasks_ws")
    demo_repo = ws_root / "demo"

    # 1. Setup CQRA-HP-05 epic: duet_harmonize
    duet_dir = demo_repo / ".devtool" / "epic" / "duet_harmonize"
    _write_epic_hld(duet_dir, "duet_harmonize")
    (duet_dir / "review_results.md").write_text(
        "# Cross-Model Review Results\n\n"
        "## Round 1\n"
        "- **SHA**: `a1b2c3d`\n"
        "- **CLI**: `codex`\n"
        "- **Model**: `gpt-5.4`\n"
        "- **Thinking**: `high`\n"
        "- **Verdict**: `AUTO_FIX_ELIGIBLE`\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 1 | Important | src/ingest.py:42 | Precedence drift across ingest sources |  |\n\n"
        "## Round 2\n"
        "- **SHA**: `e4f5a6b`\n"
        "- **CLI**: `codex`\n"
        "- **Model**: `gpt-5.4`\n"
        "- **Thinking**: `high`\n"
        "- **Verdict**: `AUTO_PASS_FINAL_MINOR_SWEEP`\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 1 | Minor | src/a.py:10 | Missing guard. Proposed: add early return |  |\n",
        encoding="utf-8",
    )
    (duet_dir / "fix_plan_round1.md").write_text(
        "# Fix Plan — Round 1\n\n"
        "## Summary Matrix\n\n"
        "| # | Severity | Location | Action |\n"
        "| --- | --- | --- | --- |\n"
        "| 1 | Important | src/ingest.py:42 | Align sidecar priority |\n\n"
        "## Detailed Plan\n\n"
        "### Finding #1\n"
        "- **Target**: `src/ingest.py:42`\n"
        "- **Proposed Action (Adjusted):** Enforce script > doc > sidecar precedence in ingest\n",
        encoding="utf-8",
    )

    # 2. Setup CQRA-FR-03 epic: broken_fp (+ additional malformed variants)
    broken_variants = {
        "broken_fp": (
            "# Truncated Fix Plan\n\n"
            "## Summary Matrix\n"
            "| # | Action\n"
            "| :--- | broken_separator |||\n"
            "| 1 |\n"
            "### Finding #1\n"
            "- **Proposed Action (Adjusted"
        ),
        "broken_pipes": (
            "|||||\n"
            "| not_an_id | ??? |\n"
            "### Fix 1 [#1]\n"
            "- **Action**:\n"
        ),
    }
    for slug, bad_fp_text in broken_variants.items():
        ep_dir = demo_repo / ".devtool" / "epic" / slug
        _write_epic_hld(ep_dir, slug)
        (ep_dir / "review_results.md").write_text(
            "## Round 1\n"
            "- **SHA**: `deadbeef`\n"
            "- **Verdict**: `CHANGES REQUIRED`\n\n"
            "| # | Severity | Location | Problem | Decision |\n"
            "|---|---|---|---|---|\n"
            "| 1 | Important | src/x.py:1 | Null deref. Proposed: guard None input | Valid |\n"
            "| 2 | Minor | src/y.py:9 | Unused helper |  |\n",
            encoding="utf-8",
        )
        (ep_dir / "fix_plan_round1.md").write_text(bad_fp_text, encoding="utf-8")

    pid_file = ws_root / "isolated_tasks_server.pid"
    port = _pick_free_port()
    server = tasks_server.TasksServer(
        host="127.0.0.1",
        port=port,
        workspace_root=ws_root,
        pid_file=pid_file,
    )
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{server.server_port}"
    ready = False
    for _ in range(50):
        try:
            with urllib.request.urlopen(f"{base_url}/api/status", timeout=0.5) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except OSError:
            time.sleep(0.05)
    assert ready, "TasksServer failed to start on isolated localhost port"

    try:
        yield {
            "ws_root": ws_root,
            "demo_repo": demo_repo,
            "base_url": base_url,
            "port": server.server_port,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3.0)


@pytest.fixture(scope="module")
def chrome_cdp_session(tmp_path_factory: pytest.TempPathFactory) -> Iterator[_CdpSession]:
    """Module-scoped headless Chrome CDP session isolated to a temporary user-data-dir."""
    chrome_bin = _find_chrome_binary()
    user_data_dir = tmp_path_factory.mktemp("cqra_chrome_profile")
    debug_port = _pick_free_port()

    proc = subprocess.Popen(
        [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--window-size=1600,1000",
            f"--user-data-dir={user_data_dir}",
            f"--remote-debugging-port={debug_port}",
            "--remote-allow-origins=*",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ws_url = ""
    for _ in range(80):
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{debug_port}/json/list", timeout=0.5
            ) as resp:
                targets = json.loads(resp.read().decode("utf-8"))
                page_targets = [
                    t
                    for t in targets
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl")
                ]
                if page_targets:
                    ws_url = str(page_targets[0]["webSocketDebuggerUrl"])
                    break
        except Exception:
            time.sleep(0.1)

    if not ws_url:
        proc.terminate()
        proc.wait(timeout=5)
        raise RuntimeError("Timed out waiting for headless Chrome /json/list page target")

    session = _CdpSession(ws_url)
    session.call("Page.enable")
    session.call("Runtime.enable")
    try:
        yield session
    finally:
        with contextlib.suppress(Exception):
            session.call("Browser.close")
        session.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _http_get_json(url: str) -> tuple[int, dict[str, Any]]:
    with urllib.request.urlopen(url, timeout=5.0) as resp:
        status = int(resp.status)
        body: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        return status, body


def _wait_for_js_condition(
    cdp: _CdpSession, js_predicate: str, timeout: float = 6.0
) -> Any:
    deadline = time.monotonic() + timeout
    last_val: Any = None
    while time.monotonic() < deadline:
        last_val = cdp.eval_js(js_predicate)
        if last_val:
            return last_val
        time.sleep(0.05)
    raise AssertionError(f"Timed out waiting for JS predicate ({js_predicate!r}); last={last_val!r}")


def test_cqra_hp_05_cross_model_proposed_action_cdp_e2e(
    tasks_e2e_workspace: dict[str, Any],
    chrome_cdp_session: _CdpSession,
) -> None:
    """[CQRA-HP-05] Cross-Model Review parser and tasks_dashboard.html populate PROPOSED ACTION from inline prefixes, 6-col tables, and fix_plan_roundN fallback."""
    base_url = tasks_e2e_workspace["base_url"]

    # 1. Verify live HTTP /api/epic/history endpoints for round_cross=1 and round_cross=2
    st_r1, hist_r1 = _http_get_json(
        f"{base_url}/api/epic/history?repo=demo&epic=duet_harmonize&round_cross=1"
    )
    st_r2, hist_r2 = _http_get_json(
        f"{base_url}/api/epic/history?repo=demo&epic=duet_harmonize&round_cross=2"
    )
    assert st_r1 == 200 and hist_r1["success"] is True
    assert st_r2 == 200 and hist_r2["success"] is True

    r1_findings = hist_r1["reviews"]["cross_model"]["findings"]
    r2_findings = hist_r2["reviews"]["cross_model"]["findings"]
    assert len(r1_findings) == 1
    assert len(r2_findings) == 1
    assert (
        r1_findings[0]["proposed_action"]
        == "Enforce script > doc > sidecar precedence in ingest"
    )
    assert r2_findings[0]["proposed_action"] == "add early return"
    assert r2_findings[0]["problem"] == "Missing guard"

    # 2. Render tasks_dashboard.html in headless Chrome via CDP and inspect DOM + computed styles
    chrome_cdp_session.console_errors.clear()
    chrome_cdp_session.uncaught_exceptions.clear()
    chrome_cdp_session.call("Page.navigate", {"url": f"{base_url}/"})
    _wait_for_js_condition(
        chrome_cdp_session,
        "document.readyState === 'complete' && typeof openEpicHistoryModal === 'function'",
    )

    # Open Epic History modal on Cross-Model Review Round 1
    chrome_cdp_session.eval_js(
        """
        (async () => {
          epicHistoryState.roundCross = 1;
          await openEpicHistoryModal('demo', 'duet_harmonize');
          switchEpicHistoryTab('cross_model');
          return true;
        })()
        """
    )

    r1_dom = _wait_for_js_condition(
        chrome_cdp_session,
        """
        (() => {
          const cell = document.querySelector('#epic-history-body table tbody tr td:nth-child(5)');
          if (!cell) return null;
          const cs = window.getComputedStyle(cell);
          const rect = cell.getBoundingClientRect();
          return {
            text: cell.textContent.trim(),
            display: cs.display,
            visibility: cs.visibility,
            width: rect.width,
            height: rect.height
          };
        })()
        """,
    )
    assert "Enforce script > doc > sidecar precedence in ingest" in r1_dom["text"]
    assert "—" not in r1_dom["text"]
    assert r1_dom["display"] != "none" and r1_dom["visibility"] == "visible"
    assert r1_dom["width"] > 0 and r1_dom["height"] > 0

    # Switch to Round 2 inside #modal-epic-history Cross-Model Review tab
    chrome_cdp_session.eval_js(
        """
        (async () => {
          await switchEpicHistoryReviewRound('cross_model', 2);
          return true;
        })()
        """
    )
    r2_dom = _wait_for_js_condition(
        chrome_cdp_session,
        """
        (() => {
          const cell = document.querySelector('#epic-history-body table tbody tr td:nth-child(5)');
          if (!cell || !cell.textContent.includes('add early return')) return null;
          const cs = window.getComputedStyle(cell);
          const rect = cell.getBoundingClientRect();
          return {
            text: cell.textContent.trim(),
            display: cs.display,
            visibility: cs.visibility,
            width: rect.width,
            height: rect.height
          };
        })()
        """,
    )
    assert r2_dom["text"] == "add early return"
    assert "—" not in r2_dom["text"]
    assert r2_dom["display"] != "none" and r2_dom["visibility"] == "visible"
    assert r2_dom["width"] > 0 and r2_dom["height"] > 0

    # Also verify standalone Cross-Model Review modal (#modal-cross-review) round transitions
    chrome_cdp_session.eval_js(
        """
        (() => {
          closeLiveModal('modal-epic-history');
          openReviewModal('demo', 'duet_harmonize', 1, 'cross-model');
          return true;
        })()
        """
    )
    standalone_r1 = _wait_for_js_condition(
        chrome_cdp_session,
        """
        (() => {
          const cell = document.querySelector('#review-findings-body tr td:nth-child(5)');
          if (!cell || cell.textContent.includes('Loading')) return null;
          return cell.textContent.trim();
        })()
        """,
    )
    assert "Enforce script > doc > sidecar precedence in ingest" in standalone_r1
    assert "—" not in standalone_r1

    chrome_cdp_session.eval_js("switchReviewRound(2)")
    standalone_r2 = _wait_for_js_condition(
        chrome_cdp_session,
        """
        (() => {
          const cell = document.querySelector('#review-findings-body tr td:nth-child(5)');
          if (!cell || !cell.textContent.includes('add early return')) return null;
          return cell.textContent.trim();
        })()
        """,
    )
    assert standalone_r2 == "add early return"
    assert "—" not in standalone_r2

    assert chrome_cdp_session.uncaught_exceptions == []
    assert chrome_cdp_session.console_errors == []


def test_cqra_ec_03_four_row_matrix_and_multiline_fix_block(tmp_path: Path) -> None:
    """[CQRA-EC-03] Multi-prefix Problem extraction preserves problem text with colons, reads best-effort fix_plan variants, and leaves empty action only when all sources omit proposals."""
    repo_dir = tmp_path / "ec03_repo"
    epic_dir = repo_dir / ".devtool" / "epic" / "ec03_epic"
    _write_epic_hld(epic_dir, "ec03_epic")

    (epic_dir / "review_results.md").write_text(
        "## Round 1\n"
        "- **SHA**: `1122334`\n"
        "- **Verdict**: `AUTO_FIX_ELIGIBLE`\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 1 | Important | src/cache.py:12 | Repeated stat calls; Suggestion: cache mtime per round file | Valid |\n"
        "| 5 | Minor | src/c.py:5 | Flag edge case: null id |  |\n"
        "| 3 | Important | tasks_server.py:527 | Stale table |  |\n\n"
        "| # | Severity | Location | Problem | Proposed Action | Decision |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| 2 | Minor | src/helper.py:8 | Raw stream read | Use bounded helper | Fixed in 9988776 |\n",
        encoding="utf-8",
    )
    (epic_dir / "fix_plan_round1.md").write_text(
        "# Round 1 Remediation Plan\n\n"
        "### Fix 3 [Important #3]: Multi-Round & Schema Robustness in `parse_review_results`\n"
        "- **Files**: `skills/check-tasks/resources/scripts/tasks_server.py`\n"
        "- **Action**:\n"
        "  - Support parsing standard `- **SHA**:`, `- **CLI**:`, `- **Model**:`, `- **Thinking**:`, `- **Verdict**:` headers.\n"
        "  - Support `round` query parameter in `/api/review?repo=<repo>&epic=<epic>&round=<N>`.\n"
        "  - Match raw output fence following `Raw output:` header.\n",
        encoding="utf-8",
    )

    parsed = tasks_server.parse_review_results(repo_dir, active_epic="ec03_epic")
    by_id = {f["id"]: f for f in parsed["findings"]}
    assert set(by_id) == {"1", "2", "3", "5"}

    # Row 1: 5-col with '; Suggestion:' prefix stripped from problem
    assert by_id["1"]["proposed_action"] == "cache mtime per round file"
    assert by_id["1"]["problem"] == "Repeated stat calls"
    assert "Suggestion:" not in by_id["1"]["problem"]

    # Row 2: 6-col explicit Proposed Action preserved separately from Decision
    assert by_id["2"]["proposed_action"] == "Use bounded helper"
    assert by_id["2"]["decision"] == "Fixed in 9988776"

    # Row 3: Problem colon preserved intact, empty proposed_action when absent everywhere
    assert by_id["5"]["proposed_action"] == ""
    assert by_id["5"]["problem"] == "Flag edge case: null id"

    # Row 4: Verbatim multi-line ### Fix 3 [Important #3] continuation bullets captured
    row4_action = by_id["3"]["proposed_action"]
    assert row4_action != ""
    assert "Support parsing standard" in row4_action
    assert "Support `round` query parameter" in row4_action
    assert "Match raw output fence" in row4_action


@pytest.mark.parametrize(
    ("problem_cell", "fix_plan_name", "fix_plan_body", "expected_problem", "expected_action"),
    [
        (
            "Prompt omits `. Proposed: <edit>` and Unproposed: label. Fix: append suffix",
            None,
            "",
            "Prompt omits `. Proposed: <edit>` and Unproposed: label",
            "append suffix",
        ),
        (
            "Thiếu kiểm tra đầu vào — Đề xuất: trả về sớm khi rỗng",
            None,
            "",
            "Thiếu kiểm tra đầu vào",
            "trả về sớm khi rỗng",
        ),
        (
            "Slow batch query. Proposed action: batch keys per chunk",
            None,
            "",
            "Slow batch query",
            "batch keys per chunk",
        ),
        (
            "Missing fallback parser",
            "fix_plan.md",
            (
                "# Unnumbered Fix Plan\n\n"
                "1. **Finding #1 (`tasks_server.py:600`)**: Parse numbered bold blocks cleanly\n"
                "   - Preserve continuation bullets until next item.\n"
                "   - **Files**: `skills/check-tasks/resources/scripts/tasks_server.py`\n"
                "2. **Finding #2 (`other.py:1`)**: Untouched second item\n"
            ),
            "Missing fallback parser",
            "Parse numbered bold blocks cleanly\n- Preserve continuation bullets until next item.",
        ),
        (
            "Colon outside bold marker",
            "fix_plan_round1.md",
            (
                "### Finding #1\n"
                "- **Proposed Action (Adjusted)**: Normalize bold colon variants\n"
                "- **Verification**: `pytest`\n"
            ),
            "Colon outside bold marker",
            "Normalize bold colon variants",
        ),
        (
            "Legacy matrix row only",
            "fix_plan_round1.md",
            (
                "## Verified Findings\n\n"
                "| # | Severity | Planned Surgical Fix |\n"
                "| --- | --- | --- |\n"
                "| #1 | Important | Guard empty slice before indexing |\n"
            ),
            "Legacy matrix row only",
            "Guard empty slice before indexing",
        ),
    ],
)
def test_cqra_ec_03_parametrized_prefixes_backticks_and_fallbacks(
    tmp_path: Path,
    problem_cell: str,
    fix_plan_name: str | None,
    fix_plan_body: str,
    expected_problem: str,
    expected_action: str,
) -> None:
    """[CQRA-EC-03] Parametrized inline code-span masking, word-boundary prefixes, numbered blocks, and Planned Surgical Fix tables."""
    repo_dir = tmp_path / "param_repo"
    epic_dir = repo_dir / ".devtool" / "epic" / "param_epic"
    _write_epic_hld(epic_dir, "param_epic")
    (epic_dir / "review_results.md").write_text(
        "## Round 1\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"| 1 | Important | src/mod.py:10 | {problem_cell} | Valid |\n",
        encoding="utf-8",
    )
    if fix_plan_name:
        (epic_dir / fix_plan_name).write_text(fix_plan_body, encoding="utf-8")

    parsed = tasks_server.parse_review_results(repo_dir, active_epic="param_epic")
    assert len(parsed["findings"]) == 1
    finding = parsed["findings"][0]
    assert finding["problem"] == expected_problem
    assert finding["proposed_action"] == expected_action


def test_cqra_ec_03_verify_sh_registers_all_five_cqra_suites() -> None:
    """[CQRA-EC-03] Verify scripts/verify.sh SUITES Section 21 registers all 5 test_cqra_*.py suites."""
    verify_text = (REPO_ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")
    expected_suites = [
        "tests/test_cqra_quota_discovery.py",
        "tests/test_cqra_refresh_session_argon.py",
        "tests/test_cqra_external_review_proposed.py",
        "tests/test_cqra_quota_ui.py",
        "tests/test_cqra_review_action_e2e.py",
    ]
    for suite_path in expected_suites:
        assert '"21", "pytest"' in verify_text
        assert suite_path in verify_text


def test_cqra_st_03_fix_plan_watch_paths_cache_invalidation(tmp_path: Path) -> None:
    """[CQRA-ST-03] Creating or modifying fix_plan_roundN.md invalidates tasks_server review parse cache immediately via watch_paths."""
    repo_dir = tmp_path / "cache_repo"
    epic_dir = repo_dir / ".devtool" / "epic" / "demo_epic"
    _write_epic_hld(epic_dir, "demo_epic")
    (epic_dir / "review_results.md").write_text(
        "## Round 1\n"
        "- **SHA**: `abcdef1`\n"
        "- **Verdict**: `AUTO_FIX_ELIGIBLE`\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 1 | Important | src/core.py:20 | Missing cache invalidation |  |\n",
        encoding="utf-8",
    )

    # 1. Initial call when fix_plan_round1.md does NOT exist yet
    res_initial = tasks_server.parse_review_results(repo_dir, active_epic="demo_epic")
    assert res_initial["findings"][0]["proposed_action"] == ""

    # 2. Create fix_plan_round1.md on disk -> must invalidate cache immediately
    fp_path = epic_dir / "fix_plan_round1.md"
    fp_path.write_text(
        "### Finding #1\n- **Proposed Action:** Initial fix\n",
        encoding="utf-8",
    )
    res_created = tasks_server.parse_review_results(repo_dir, active_epic="demo_epic")
    assert res_created["findings"][0]["proposed_action"] == "Initial fix"

    # 3. Edit fix_plan_round1.md on disk with distinct mtime -> must invalidate cache immediately
    st_before = fp_path.stat()
    fp_path.write_text(
        "### Finding #1\n- **Proposed Action:** Updated fix action\n",
        encoding="utf-8",
    )
    os.utime(
        fp_path,
        ns=(st_before.st_atime_ns, st_before.st_mtime_ns + 50_000_000),
    )
    res_updated = tasks_server.parse_review_results(repo_dir, active_epic="demo_epic")
    assert res_updated["findings"][0]["proposed_action"] == "Updated fix action"


@pytest.mark.parametrize("epic_slug", ["broken_fp", "broken_pipes"])
def test_cqra_fr_03_malformed_fix_plan_resilience(
    tasks_e2e_workspace: dict[str, Any],
    epic_slug: str,
) -> None:
    """[CQRA-FR-03] Malformed fix_plan_roundN.md alongside valid review_results.md degrades per-file without breaking TasksServer endpoints."""
    base_url = tasks_e2e_workspace["base_url"]

    st_rev, rev_json = _http_get_json(f"{base_url}/api/review?repo=demo&epic={epic_slug}")
    assert st_rev == 200
    assert rev_json["present"] is True
    assert "CHANGES REQUIRED" in rev_json["verdict"]
    assert len(rev_json["findings"]) == 2
    assert rev_json["findings"][0]["proposed_action"] == "guard None input"
    assert rev_json["findings"][0]["problem"] == "Null deref"
    assert rev_json["findings"][1]["proposed_action"] == ""

    st_hist, hist_json = _http_get_json(
        f"{base_url}/api/epic/history?repo=demo&epic={epic_slug}"
    )
    assert st_hist == 200
    assert hist_json["success"] is True
    cross = hist_json["reviews"]["cross_model"]
    assert cross["present"] is True
    assert cross["findings"][0]["proposed_action"] == "guard None input"
    assert cross["findings"][1]["proposed_action"] == ""
