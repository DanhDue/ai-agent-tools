"""Browser DOM and Headless Chrome CDP tests for Quota Dashboard Dynamic UI (Task 04).

Covers:
- [CQRA-HP-03] Dynamic badges, per-group rosters, Shared w/ Gemini Pool mirror, and modal
- [CQRA-EC-02] Legacy cached payloads without new model fields and none-Argon accounts
- [CQRA-AR-02] Quota score 4-bucket formula keeps Argon excluded while preserving ARGON filter
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_HTML_PATH = (
    REPO_ROOT
    / "skills"
    / "check-quota"
    / "resources"
    / "dashboard"
    / "quota_dashboard.html"
)
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import agy_quota  # type: ignore[import-not-found]  # noqa: E402


def _find_chrome_binary() -> str:
    env_bin = os.environ.get("CHROME_BIN")
    if env_bin and Path(env_bin).exists():
        return env_bin
    for candidate in (
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    pytest.skip("Headless Chrome binary not available on this host")
    raise RuntimeError("Unreachable")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class _CdpWebSocket:
    """Minimal RFC 6455 WebSocket client over localhost TCP for Chrome DevTools Protocol."""

    def __init__(self, ws_url: str, timeout: float = 10.0) -> None:
        parsed = urllib.parse.urlparse(ws_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 80
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        self._sock = socket.create_connection((host, port), timeout=timeout)
        self._sock.settimeout(timeout)
        self._buffer = bytearray()

        raw_key = base64.b64encode(os.urandom(16)).decode("ascii")
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {raw_key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self._sock.sendall(handshake.encode("ascii"))

        while b"\r\n\r\n" not in self._buffer:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise RuntimeError("CDP WebSocket closed before handshake completed")
            self._buffer.extend(chunk)

        header_end = self._buffer.index(b"\r\n\r\n") + 4
        header_bytes = bytes(self._buffer[:header_end])
        del self._buffer[:header_end]

        status_line = header_bytes.split(b"\r\n", 1)[0].decode("latin1")
        if "101" not in status_line:
            raise RuntimeError(f"CDP WebSocket handshake failed: {status_line}")
        expected_accept = base64.b64encode(
            hashlib.sha1(
                (raw_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")
            ).digest()
        ).decode("ascii")
        if expected_accept.encode("ascii") not in header_bytes:
            raise RuntimeError("CDP WebSocket Sec-WebSocket-Accept mismatch")

    def _read_exact(self, length: int) -> bytes:
        while len(self._buffer) < length:
            chunk = self._sock.recv(max(4096, length - len(self._buffer)))
            if not chunk:
                raise RuntimeError("CDP WebSocket connection closed unexpectedly")
            self._buffer.extend(chunk)
        out = bytes(self._buffer[:length])
        del self._buffer[:length]
        return out

    def send_text(self, payload: str) -> None:
        data = payload.encode("utf-8")
        mask_key = os.urandom(4)
        length = len(data)
        header = bytearray([0x81])
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack(">H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack(">Q", length))
        masked = bytes(b ^ mask_key[idx % 4] for idx, b in enumerate(data))
        self._sock.sendall(bytes(header) + mask_key + masked)

    def recv_text(self) -> str:
        fragments: list[bytes] = []
        while True:
            b0, b1 = self._read_exact(2)
            fin = bool(b0 & 0x80)
            opcode = b0 & 0x0F
            masked = bool(b1 & 0x80)
            length = b1 & 0x7F
            if length == 126:
                (length,) = struct.unpack(">H", self._read_exact(2))
            elif length == 127:
                (length,) = struct.unpack(">Q", self._read_exact(8))
            mask_key = self._read_exact(4) if masked else b""
            payload = self._read_exact(length)
            if masked:
                payload = bytes(b ^ mask_key[idx % 4] for idx, b in enumerate(payload))

            if opcode == 0x8:
                raise RuntimeError("CDP WebSocket closed by Chrome")
            if opcode == 0x9:
                pong = bytearray([0x8A, 0x80 | len(payload)])
                pong_mask = os.urandom(4)
                pong_body = bytes(
                    b ^ pong_mask[idx % 4] for idx, b in enumerate(payload)
                )
                self._sock.sendall(bytes(pong) + pong_mask + pong_body)
                continue
            if opcode in (0x0, 0x1):
                fragments.append(payload)
                if fin:
                    return b"".join(fragments).decode("utf-8")

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass


@dataclass
class CdpHarness:
    """Module-scoped Chrome CDP client with Zero-Console-Error watchdog."""

    ws: _CdpWebSocket
    base_url: str
    repo_html_sha256: str
    console_errors: list[str] = field(default_factory=list)
    page_exceptions: list[str] = field(default_factory=list)
    _msg_id: int = 0

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._msg_id += 1
        target_id = self._msg_id
        self.ws.send_text(
            json.dumps({"id": target_id, "method": method, "params": params or {}})
        )
        while True:
            raw = self.ws.recv_text()
            msg: dict[str, Any] = json.loads(raw)
            self._record_event(msg)
            if msg.get("id") == target_id:
                if "error" in msg:
                    raise RuntimeError(f"CDP {method} error: {msg['error']}")
                result: dict[str, Any] = msg.get("result", {})
                return result

    def _record_event(self, msg: dict[str, Any]) -> None:
        method = msg.get("method")
        params = msg.get("params", {})
        if method == "Runtime.consoleAPICalled" and params.get("type") == "error":
            args = params.get("args", [])
            rendered = " ".join(
                str(a.get("value") or a.get("description") or a) for a in args
            )
            self.console_errors.append(rendered)
        elif method == "Runtime.exceptionThrown":
            details = params.get("exceptionDetails", {})
            exc = details.get("exception", {})
            desc = str(exc.get("description") or details.get("text") or details)
            self.page_exceptions.append(desc)

    def eval_js(self, expression: str) -> Any:
        res = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )
        if "exceptionDetails" in res:
            details = res["exceptionDetails"]
            self.page_exceptions.append(str(details))
            raise AssertionError(f"Uncaught JS evaluation exception: {details}")
        inner: dict[str, Any] = res.get("result", {})
        return inner.get("value")

    def assert_zero_console_errors(self) -> None:
        assert self.console_errors == [], (
            f"Unexpected console.error logs: {self.console_errors}"
        )
        assert self.page_exceptions == [], (
            f"Unexpected page exceptions: {self.page_exceptions}"
        )


def _build_fixture_profiles() -> dict[str, dict[str, Any]]:
    groups_shared = [
        {
            "name": "Gemini Models",
            "description": (
                "Gemini 4 Carbon, Gemini 4 Argon, Gemini 4 Hydrogen, "
                "Orchestrator (Carbon), Orchestrator (Argon), Gemini 3.8 Flash"
            ),
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.90,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 0.85,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
        {
            "name": "Claude and GPT models",
            "description": "Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.92,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 0.90,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
    ]
    usage_shared = agy_quota.parse_usage_group_models(groups_shared)
    catalog_shared = agy_quota.parse_agy_models_catalog(
        "\n".join(
            [
                "gemini-4-carbon-high",
                "gemini-4-argon-high",
                "gemini-pro-orchestrator",
                "gemini-pro-orchestrator-argon",
            ]
        )
    )
    shared_profile = agy_quota.format_profile_for_dashboard(
        "nguyenhieu000690",
        {
            "success": True,
            "email": "nguyenhieu000690@gmail.com",
            "plan_name": "Google AI Ultra",
            "groups": groups_shared,
            "items": agy_quota.parse_quota_items(groups_shared),
            "groupModels": usage_shared["groupModels"],
            "groupDescSig": usage_shared["groupDescSig"],
            "availableModels": [
                "gemini-4-carbon-high",
                "gemini-4-argon-high",
                "gemini-pro-orchestrator",
                "gemini-pro-orchestrator-argon",
            ],
            "modelCatalog": catalog_shared,
            "modelsFetchedAt": "2026-11-18T00:00:00Z",
        },
    )

    groups_separate = [
        {
            "name": "Gemini Models",
            "description": "Gemini 4 Hydrogen, Gemini 3.8 Flash",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 1.0,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 1.0,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
        {
            "name": "Claude and GPT models",
            "description": "Claude Opus 5.5, Claude Sonnet 5.5, GPT-OSS 120B",
            "buckets": [
                {
                    "window": "5h",
                    "remaining_fraction": 0.80,
                    "reset_time": "2026-11-18T10:00:00Z",
                },
                {
                    "window": "weekly",
                    "remaining_fraction": 0.80,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
        {
            "name": "Gemini 4 Argon",
            "description": "Gemini 4 Argon",
            "buckets": [
                {
                    "window": "weekly",
                    "remaining_fraction": 0.45,
                    "reset_time": "2026-11-24T00:00:00Z",
                },
            ],
        },
    ]
    usage_separate = agy_quota.parse_usage_group_models(groups_separate)
    catalog_separate = agy_quota.parse_agy_models_catalog(
        "\n".join(
            [
                "gemini-4-hydrogen-high",
                "gemini-4-argon-high",
                "gemini-pro-orchestrator-g1-pro",
            ]
        )
    )
    separate_profile = agy_quota.format_profile_for_dashboard(
        "danhdue",
        {
            "success": True,
            "email": "danhdue@gmail.com",
            "plan_name": "Google AI Pro",
            "groups": groups_separate,
            "items": agy_quota.parse_quota_items(groups_separate),
            "groupModels": usage_separate["groupModels"],
            "groupDescSig": usage_separate["groupDescSig"],
            "availableModels": [
                "gemini-4-hydrogen-high",
                "gemini-4-argon-high",
                "gemini-pro-orchestrator-g1-pro",
            ],
            "modelCatalog": catalog_separate,
            "modelsFetchedAt": "2026-11-18T01:00:00Z",
        },
    )

    legacy_cached: dict[str, Any] = {
        "email": "legacy_cached@gmail.com",
        "tier": "PRO",
        "priority": 50,
        "status": "ACTIVE",
        "isAppeal": False,
        "hasArgon": True,
        "gemini5h": {
            "name": "Gemini 3.8 / Pro 5H",
            "fraction": 0.75,
            "countdown": "⏱ 3h 20m",
            "resetTime": "2026-11-18T09:00:00Z",
            "unavailable": False,
        },
        "claude5h": {
            "name": "Claude 5.5 / GPT 5H",
            "fraction": 0.65,
            "countdown": "⏱ 3h 20m",
            "resetTime": "2026-11-18T09:00:00Z",
            "unavailable": False,
        },
        "geminiWeekly": {
            "name": "Gemini Weekly",
            "fraction": 0.70,
            "countdown": "⏱ 5d 10h",
            "resetTime": "2026-11-23T00:00:00Z",
            "unavailable": False,
        },
        "claudeWeekly": {
            "name": "Claude Weekly",
            "fraction": 0.60,
            "countdown": "⏱ 5d 10h",
            "resetTime": "2026-11-23T00:00:00Z",
            "unavailable": False,
        },
        "argonWeekly": {
            "name": "Gemini 4 Argon Weekly",
            "fraction": 0.30,
            "countdown": "⏱ 5d 10h",
            "resetTime": "2026-11-23T00:00:00Z",
            "unavailable": False,
            "tags": True,
        },
    }

    free_acct: dict[str, Any] = {
        "email": "free_acct@gmail.com",
        "tier": "FREE",
        "priority": 20,
        "status": "ACTIVE",
        "isAppeal": False,
        "hasArgon": False,
        "gemini5h": {
            "name": "Gemini 3.8 / Pro 5H",
            "fraction": 1.0,
            "countdown": "⏱ 4h 59m",
            "resetTime": "",
            "unavailable": True,
        },
        "claude5h": {
            "name": "Claude 5.5 / GPT 5H",
            "fraction": 1.0,
            "countdown": "⏱ 4h 59m",
            "resetTime": "",
            "unavailable": True,
        },
        "geminiWeekly": {
            "name": "Gemini Weekly",
            "fraction": 1.0,
            "countdown": "⏱ 6d 20h",
            "resetTime": "2026-11-24T00:00:00Z",
            "unavailable": False,
        },
        "claudeWeekly": {
            "name": "Claude Weekly",
            "fraction": 1.0,
            "countdown": "⏱ 6d 20h",
            "resetTime": "2026-11-24T00:00:00Z",
            "unavailable": False,
        },
        "argonWeekly": {
            "name": "Gemini 4 Argon Weekly",
            "fraction": 0.0,
            "countdown": "Unavailable N/A",
            "resetTime": "",
            "unavailable": True,
            "tags": True,
            "sharedPool": False,
            "mode": "none",
        },
        "groupModels": {"gemini": ["Gemini 3.8 Flash"], "claude": [], "argon": []},
        "capabilities": {
            "tier": "FREE",
            "hasCarbon": False,
            "hasArgon": False,
            "argonMode": "none",
            "hasOrchestrator": False,
            "badges": ["FREE"],
        },
        "modelsFetchedAt": "2026-11-18T02:00:00Z",
        "groupDescSig": "free0000sig12345",
    }

    xss_probe: dict[str, Any] = {
        "email": "xss_probe@gmail.com",
        "tier": "PRO",
        "priority": 50,
        "status": "ACTIVE",
        "isAppeal": False,
        "hasArgon": False,
        "gemini5h": {
            "name": "Gemini 3.8 / Pro 5H",
            "fraction": 0.50,
            "countdown": "⏱ 2h 00m",
            "resetTime": "2026-11-18T08:00:00Z",
            "unavailable": False,
        },
        "claude5h": {
            "name": "Claude 5.5 / GPT 5H",
            "fraction": 0.50,
            "countdown": "⏱ 2h 00m",
            "resetTime": "2026-11-18T08:00:00Z",
            "unavailable": False,
        },
        "geminiWeekly": {
            "name": "Gemini Weekly",
            "fraction": 0.50,
            "countdown": "⏱ 4d 0h",
            "resetTime": "2026-11-22T00:00:00Z",
            "unavailable": False,
        },
        "claudeWeekly": {
            "name": "Claude Weekly",
            "fraction": 0.50,
            "countdown": "⏱ 4d 0h",
            "resetTime": "2026-11-22T00:00:00Z",
            "unavailable": False,
        },
        "argonWeekly": {
            "name": "Gemini 4 Argon Weekly",
            "fraction": 0.0,
            "countdown": "Unavailable N/A",
            "resetTime": "",
            "unavailable": True,
            "tags": True,
            "sharedPool": False,
            "mode": "none",
        },
        "groupModels": {
            "gemini": ["<img src=x onerror=window.__xss=1>"],
            "claude": ["Claude <b>4.6</b>"],
            "argon": [],
        },
        "capabilities": {
            "tier": "PRO",
            "hasCarbon": False,
            "hasArgon": False,
            "argonMode": "none",
            "hasOrchestrator": False,
            "badges": ["PRO", "<script>window.__xss=2</script>"],
        },
        "modelsFetchedAt": "2026-11-18T02:30:00Z",
        "groupDescSig": "sig<xss>&quote",
    }

    return {
        "nguyenhieu000690": shared_profile,
        "danhdue": separate_profile,
        "legacy_cached": legacy_cached,
        "free_acct": free_acct,
        "xss_probe": xss_probe,
    }


@pytest.fixture(scope="module")
def quota_cdp_harness(tmp_path_factory: pytest.TempPathFactory) -> Iterator[CdpHarness]:
    """Serve isolated tmp_path quota_dashboard.html and attach headless Chrome CDP."""
    chrome_bin = _find_chrome_binary()
    tmp_dir = tmp_path_factory.mktemp("cqra_quota_dashboard_ui")
    chrome_profile_dir = tmp_path_factory.mktemp("cqra_chrome_profile")

    raw_html = DASHBOARD_HTML_PATH.read_text(encoding="utf-8")
    repo_sha_before = hashlib.sha256(raw_html.encode("utf-8")).hexdigest()

    profiles = _build_fixture_profiles()
    safe_profiles_js = json.dumps(profiles, ensure_ascii=False, indent=2).replace(
        "</", "<\\/"
    )
    injected_html, count = re.subn(
        r"const PROFILES_DATA = \{.*?\n\};",
        f"const PROFILES_DATA = {safe_profiles_js}\n;",
        raw_html,
        count=1,
        flags=re.DOTALL,
    )
    assert count == 1, (
        "Failed to inject PROFILES_DATA into isolated quota_dashboard.html copy"
    )
    isolated_html_path = tmp_dir / "quota_dashboard.html"
    isolated_html_path.write_text(injected_html, encoding="utf-8")

    status_payload = json.dumps(
        {
            "success": True,
            "profiles": profiles,
            "schedules_by_profile": {},
            "can_auto_refresh": False,
            "last_refresh_all": 1763424000,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    html_bytes = injected_html.encode("utf-8")

    class _DashboardRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path in ("/", "/quota_dashboard.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_bytes)))
                self.end_headers()
                self.wfile.write(html_bytes)
                return
            if parsed.path == "/api/status":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(status_payload)))
                self.end_headers()
                self.wfile.write(status_payload)
                return
            if parsed.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), _DashboardRequestHandler)
    http_port = int(server.server_address[1])
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    cdp_port = _find_free_port()
    chrome_proc = subprocess.Popen(
        [
            chrome_bin,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--window-size=1440,900",
            f"--user-data-dir={chrome_profile_dir}",
            f"--remote-debugging-port={cdp_port}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ws: _CdpWebSocket | None = None
    try:
        ws_url = ""
        deadline = time.monotonic() + 12.0
        while time.monotonic() < deadline:
            try:
                raw_targets = urllib.request.urlopen(
                    f"http://127.0.0.1:{cdp_port}/json/list", timeout=1.0
                ).read()
                targets = json.loads(raw_targets.decode("utf-8"))
                page_targets = [
                    t
                    for t in targets
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl")
                ]
                if page_targets:
                    ws_url = str(page_targets[0]["webSocketDebuggerUrl"])
                    break
            except Exception:
                time.sleep(0.15)
        assert ws_url, "Failed to obtain Chrome CDP page webSocketDebuggerUrl"

        ws = _CdpWebSocket(ws_url)
        base_url = (
            f"http://127.0.0.1:{http_port}/quota_dashboard.html?no-auto-refresh=1"
        )
        harness = CdpHarness(ws=ws, base_url=base_url, repo_html_sha256=repo_sha_before)
        harness.call("Network.enable")
        harness.call("Network.setBlockedURLs", {"urls": ["https://www.gstatic.com/*"]})
        harness.call("Page.enable")
        harness.call("Runtime.enable")
        harness.call("DOM.enable")
        harness.call("Page.navigate", {"url": base_url})

        ready = False
        nav_deadline = time.monotonic() + 10.0
        while time.monotonic() < nav_deadline:
            state = harness.eval_js(
                "document.readyState === 'complete' "
                "&& Boolean(document.getElementById('card-nguyenhieu000690'))"
            )
            if state is True:
                ready = True
                break
            time.sleep(0.15)
        assert ready, "Dashboard page did not finish rendering #card-nguyenhieu000690"

        yield harness

        repo_sha_after = hashlib.sha256(DASHBOARD_HTML_PATH.read_bytes()).hexdigest()
        assert repo_sha_after == repo_sha_before, (
            "Repo-tracked quota_dashboard.html was mutated during test execution"
        )
    finally:
        if ws is not None:
            ws.close()
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()
        server.shutdown()
        server.server_close()


def test_cqra_hp_03_quota_dashboard_cdp_dynamic_badges_and_shared_pool(
    quota_cdp_harness: CdpHarness,
) -> None:
    """[CQRA-HP-03] Render dynamic badges, per-group rosters, Shared Gemini Pool row, and modal."""
    quota_cdp_harness.assert_zero_console_errors()

    dom_snapshot: dict[str, Any] = quota_cdp_harness.eval_js(
        """(() => {
          const sharedCard = document.getElementById('card-nguyenhieu000690');
          const separateCard = document.getElementById('card-danhdue');
          if (!sharedCard || !separateCard) return { missingCards: true };

          const sharedHeader = sharedCard.querySelector('.border-b');
          const separateHeader = separateCard.querySelector('.border-b');
          const sharedArgonBadge = sharedHeader
            ? Array.from(sharedHeader.querySelectorAll('.pill-badge'))
                .find((el) => el.textContent.includes('Argon'))
            : null;
          const separateArgonBadge = separateHeader
            ? Array.from(separateHeader.querySelectorAll('.pill-badge'))
                .find((el) => el.textContent.includes('Argon'))
            : null;

          const sharedModelCards = Array.from(sharedCard.querySelectorAll('.model-card-item'));
          const sharedArgonRow = sharedModelCards[sharedModelCards.length - 1];
          const separateModelCards = Array.from(separateCard.querySelectorAll('.model-card-item'));
          const separateArgonRow = separateModelCards[separateModelCards.length - 1];

          const rect = sharedCard.getBoundingClientRect();
          const computed = window.getComputedStyle(sharedCard);

          openProfileInfoModal('nguyenhieu000690');
          const outerModal = document.getElementById('profileInfoModal');
          const innerModal = document.getElementById('profile-info-modal');
          const outerDisplay = outerModal ? window.getComputedStyle(outerModal).display : 'missing';
          const modalRect = innerModal ? innerModal.getBoundingClientRect() : null;
          const modalText = innerModal ? innerModal.textContent : '';
          closeProfileInfoModal();

          return {
            missingCards: false,
            sharedHeaderText: sharedHeader ? sharedHeader.textContent : '',
            separateHeaderText: separateHeader ? separateHeader.textContent : '',
            sharedArgonTooltip: sharedArgonBadge ? (sharedArgonBadge.getAttribute('title') || '') : '',
            separateArgonTooltip: separateArgonBadge
              ? (separateArgonBadge.getAttribute('title') || '')
              : '',
            sharedCardText: sharedCard.textContent || '',
            separateCardText: separateCard.textContent || '',
            sharedArgonRowText: sharedArgonRow ? sharedArgonRow.textContent : '',
            separateArgonRowText: separateArgonRow ? separateArgonRow.textContent : '',
            cardWidth: rect.width,
            cardHeight: rect.height,
            cardDisplay: computed.display,
            overflowDelta: sharedCard.scrollWidth - sharedCard.clientWidth,
            outerDisplay,
            modalWidth: modalRect ? modalRect.width : 0,
            modalHeight: modalRect ? modalRect.height : 0,
            modalText,
            expectedSig: PROFILES_DATA['nguyenhieu000690'].groupDescSig || '',
          };
        })()"""
    )

    assert dom_snapshot["missingCards"] is False
    for expected_badge in ("ULTRA", "Carbon", "Argon", "Orchestrator"):
        assert expected_badge in dom_snapshot["sharedHeaderText"], (
            f"Missing badge {expected_badge!r} in shared card header: "
            f"{dom_snapshot['sharedHeaderText']!r}"
        )
    assert dom_snapshot["sharedArgonTooltip"] == "Shared w/ Gemini Pool"

    for expected_sep_badge in ("PRO", "Argon", "Orchestrator"):
        assert expected_sep_badge in dom_snapshot["separateHeaderText"]
    assert "ULTRA" not in dom_snapshot["separateHeaderText"]
    assert "Carbon" not in dom_snapshot["separateHeaderText"]
    assert dom_snapshot["separateArgonTooltip"] == ""

    for gemini_model in (
        "Gemini 4 Carbon",
        "Gemini 4 Argon",
        "Gemini 4 Hydrogen",
        "Orchestrator (Carbon)",
        "Orchestrator (Argon)",
        "Gemini 3.8 Flash",
    ):
        assert gemini_model in dom_snapshot["sharedCardText"]
    for claude_model in ("Claude Sonnet 4.6", "Claude Opus 4.6", "GPT-OSS 120B"):
        assert claude_model in dom_snapshot["sharedCardText"]
    for sep_claude_model in ("Claude Opus 5.5", "Claude Sonnet 5.5", "GPT-OSS 120B"):
        assert sep_claude_model in dom_snapshot["separateCardText"]

    argon_row_text = dom_snapshot["sharedArgonRowText"]
    assert "Shared w/ Gemini Pool" in argon_row_text
    assert "85%" in argon_row_text
    assert "INACTIVE" not in argon_row_text
    assert "Unavailable N/A" not in argon_row_text

    assert "Shared w/ Gemini Pool" not in dom_snapshot["separateArgonRowText"]
    assert "45%" in dom_snapshot["separateArgonRowText"]

    assert dom_snapshot["cardWidth"] > 240
    assert dom_snapshot["cardHeight"] > 180
    assert dom_snapshot["cardDisplay"] == "flex"
    assert dom_snapshot["overflowDelta"] <= 2

    assert dom_snapshot["outerDisplay"] != "none"
    assert dom_snapshot["modalWidth"] > 240
    assert dom_snapshot["modalHeight"] > 180

    modal_text = dom_snapshot["modalText"]
    for heading in ("Gemini Models", "Claude & GPT", "Argon / Orchestrator"):
        assert heading in modal_text, (
            f"Missing modal section {heading!r} in {modal_text!r}"
        )
    for expected_token in (
        "Gemini 4 Carbon",
        "Gemini 4 Argon",
        "Gemini 4 Hydrogen",
        "Orchestrator (Carbon)",
        "Orchestrator (Argon)",
        "Gemini 3.8 Flash",
        "Claude Sonnet 4.6",
        "Claude Opus 4.6",
        "GPT-OSS 120B",
        "shared_gemini",
        "2026-11-18T00:00:00Z",
        dom_snapshot["expectedSig"],
    ):
        assert expected_token and expected_token in modal_text

    quota_cdp_harness.assert_zero_console_errors()


class Test_Integration:
    """[Tier C - Integration] Headless Chrome CDP integration suite provenance for CQRA-HP-03."""

    def test_cqra_hp_03_integration(self, quota_cdp_harness: CdpHarness) -> None:
        """[CQRA-HP-03] Execute headless Chrome CDP integration verification."""
        test_cqra_hp_03_quota_dashboard_cdp_dynamic_badges_and_shared_pool(
            quota_cdp_harness
        )


@pytest.mark.parametrize(
    ("profile_key", "expected_present", "expected_absent", "expected_min_score"),
    [
        (
            "legacy_cached",
            (
                "Gemini 3.8 / Pro 5H",
                "Claude 5.5 / GPT 5H",
                "Gemini Weekly",
                "Claude Weekly",
            ),
            ("Shared w/ Gemini Pool", "undefined", "NaN"),
            60.0,
        ),
        (
            "free_acct",
            ("FREE", "Gemini Weekly", "Claude Weekly"),
            ("Shared w/ Gemini Pool", "✣"),
            40.0,
        ),
        (
            "xss_probe",
            ("<img src=x onerror=window.__xss=1>", "Claude <b>4.6</b>"),
            ("Shared w/ Gemini Pool", "✣"),
            45.0,
        ),
    ],
)
def test_cqra_ec_02_legacy_payload_and_none_argon_safe_dom(
    quota_cdp_harness: CdpHarness,
    profile_key: str,
    expected_present: tuple[str, ...],
    expected_absent: tuple[str, ...],
    expected_min_score: float,
) -> None:
    """[CQRA-EC-02] Legacy cached payloads and none-Argon accounts render safely without errors."""
    result: dict[str, Any] = quota_cdp_harness.eval_js(
        f"""(() => {{
          const key = {json.dumps(profile_key)};
          const data = PROFILES_DATA[key];
          const html = renderProfileCard(key, data);
          const score = getProfileQuotaScore(key);
          const card = document.getElementById('card-' + key);
          const rect = card ? card.getBoundingClientRect() : {{ width: 0, height: 0 }};
          const headerText = card && card.querySelector('.border-b')
            ? card.querySelector('.border-b').textContent
            : '';
          openProfileInfoModal(key);
          const innerModal = document.getElementById('profile-info-modal')
            || document.getElementById('profileInfoModal');
          const injectedElements = (card ? card.querySelectorAll('img, script').length : 0)
            + (innerModal ? innerModal.querySelectorAll('img, script').length : 0);
          closeProfileInfoModal();
          return {{
            renderedLength: html.trim().length,
            cardText: card ? card.textContent : '',
            headerText,
            score,
            width: rect.width,
            height: rect.height,
            xssFlag: Boolean(window.__xss),
            injectedElements,
          }};
        }})()"""
    )

    assert result["renderedLength"] > 100
    assert result["width"] > 200
    assert result["height"] > 120
    assert float(result["score"]) >= expected_min_score
    assert result["xssFlag"] is False
    assert result["injectedElements"] == 0

    for token in expected_present:
        assert token in result["cardText"], (
            f"Expected {token!r} in {profile_key} card text"
        )
    for forbidden in expected_absent:
        assert forbidden not in result["cardText"], (
            f"Unexpected {forbidden!r} in {profile_key} card text"
        )
    if profile_key == "free_acct":
        assert "Argon" not in result["headerText"]

    quota_cdp_harness.assert_zero_console_errors()


@pytest.mark.parametrize(
    (
        "argon_fraction",
        "shared_pool",
        "argon_mode",
        "has_argon",
        "unavailable",
        "expect_argon",
    ),
    [
        (0.80, True, "shared_gemini", True, False, True),
        (0.20, False, "separate", True, False, True),
        (0.0, False, "none", False, True, False),
    ],
)
def test_cqra_ar_02_quota_score_excludes_argon_and_preserves_filter(
    quota_cdp_harness: CdpHarness,
    argon_fraction: float,
    shared_pool: bool,
    argon_mode: str,
    has_argon: bool,
    unavailable: bool,
    expect_argon: bool,
) -> None:
    """[CQRA-AR-02] Keep 4-bucket quota score equal at 80.0 and preserve ARGON filter match."""
    eval_out: dict[str, Any] = quota_cdp_harness.eval_js(
        f"""(() => {{
          const probeId = 'ar02_probe';
          const prevStatus = document.getElementById('statusFilter').value;
          const prevShared = PROFILES_DATA['nguyenhieu000690'];
          try {{
            PROFILES_DATA['nguyenhieu000690'] = {{
              ...prevShared,
              tier: 'PRO',
              status: 'ACTIVE',
              hasArgon: true,
              gemini5h: {{ name: 'Gemini 3.8 / Pro 5H', fraction: 0.80, countdown: '⏱ 4h', unavailable: false }},
              claude5h: {{ name: 'Claude 5.5 / GPT 5H', fraction: 0.80, countdown: '⏱ 4h', unavailable: false }},
              geminiWeekly: {{ name: 'Gemini Weekly', fraction: 0.80, countdown: '⏱ 5d', unavailable: false }},
              claudeWeekly: {{ name: 'Claude Weekly', fraction: 0.80, countdown: '⏱ 5d', unavailable: false }},
              argonWeekly: {{
                name: 'Gemini 4 Argon Weekly',
                fraction: 0.80,
                countdown: '⏱ 5d',
                unavailable: false,
                sharedPool: true,
                mode: 'shared_gemini',
              }},
              capabilities: {{
                tier: 'ULTRA',
                hasCarbon: true,
                hasArgon: true,
                argonMode: 'shared_gemini',
                hasOrchestrator: true,
                badges: ['ULTRA', 'Carbon', 'Argon', 'Orchestrator'],
              }},
            }};
            PROFILES_DATA[probeId] = {{
              email: 'probe@gmail.com',
              tier: {json.dumps("FREE" if argon_mode == "none" else "PRO")},
              status: 'ACTIVE',
              hasArgon: {json.dumps(has_argon)},
              gemini5h: {{ name: 'Gemini 3.8 / Pro 5H', fraction: 0.80, countdown: '⏱ 4h', unavailable: false }},
              claude5h: {{ name: 'Claude 5.5 / GPT 5H', fraction: 0.80, countdown: '⏱ 4h', unavailable: false }},
              geminiWeekly: {{ name: 'Gemini Weekly', fraction: 0.80, countdown: '⏱ 5d', unavailable: false }},
              claudeWeekly: {{ name: 'Claude Weekly', fraction: 0.80, countdown: '⏱ 5d', unavailable: false }},
              argonWeekly: {{
                name: 'Gemini 4 Argon Weekly',
                fraction: {json.dumps(argon_fraction)},
                countdown: {json.dumps("Unavailable N/A" if unavailable else "⏱ 5d")},
                unavailable: {json.dumps(unavailable)},
                sharedPool: {json.dumps(shared_pool)},
                mode: {json.dumps(argon_mode)},
              }},
              capabilities: {{
                tier: {json.dumps("FREE" if argon_mode == "none" else "PRO")},
                hasCarbon: false,
                hasArgon: {json.dumps(has_argon)},
                argonMode: {json.dumps(argon_mode)},
                hasOrchestrator: false,
                badges: {json.dumps(["FREE"] if argon_mode == "none" else ["PRO", "Argon"])},
              }},
            }};

            const sharedScore = getProfileQuotaScore('nguyenhieu000690');
            const probeScore = getProfileQuotaScore(probeId);
            const sharedSchedulable = isProfileSchedulable(
              'nguyenhieu000690',
              PROFILES_DATA['nguyenhieu000690']
            );
            const probeSchedulable = isProfileSchedulable(probeId, PROFILES_DATA[probeId]);

            document.getElementById('statusFilter').value = 'ARGON';
            filterProfiles();
            const sharedInArgonFilter = Boolean(document.getElementById('card-nguyenhieu000690'));
            const probeInArgonFilter = Boolean(document.getElementById('card-' + probeId));
            const sharedText = document.getElementById('card-nguyenhieu000690')
              ? document.getElementById('card-nguyenhieu000690').textContent
              : '';
            return {{
              sharedScore,
              probeScore,
              sharedSchedulable,
              probeSchedulable,
              sharedInArgonFilter,
              probeInArgonFilter,
              sharedText,
            }};
          }} finally {{
            delete PROFILES_DATA[probeId];
            PROFILES_DATA['nguyenhieu000690'] = prevShared;
            document.getElementById('statusFilter').value = prevStatus;
            filterProfiles();
          }}
        }})()"""
    )

    assert float(eval_out["sharedScore"]) == pytest.approx(80.0)
    assert float(eval_out["probeScore"]) == pytest.approx(80.0)
    assert eval_out["sharedInArgonFilter"] is True
    assert eval_out["sharedSchedulable"] is True
    assert eval_out["probeInArgonFilter"] is expect_argon
    assert eval_out["probeSchedulable"] is (argon_mode != "none")
    assert "hoangcongtam690" not in eval_out["sharedText"]

    quota_cdp_harness.assert_zero_console_errors()
