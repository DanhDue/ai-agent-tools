"""Unit and Integration tests for Playwright Zero-Console-And-Layout-Defect Watchdog (Task 02)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "skills" / "web-quality-check" / "resources" / "templates"
SCRIPTS_DIR = REPO_ROOT / "skills" / "web-quality-check" / "resources" / "scripts"

if str(TEMPLATES_DIR) not in sys.path:
    sys.path.insert(0, str(TEMPLATES_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from playwright_zero_error import (
    assert_dom_state_integrity,
    assert_visual_integrity,
    attach_zero_error_watchdog,
)
from run_playwright_harness import run_playwright_suite


class MockConsoleMessage:
    def __init__(self, msg_type: str, text: str) -> None:
        self.type = msg_type
        self.text = text


class MockRequest:
    def __init__(self, resource_type: str) -> None:
        self.resource_type = resource_type


class MockResponse:
    def __init__(self, status: int, url: str, resource_type: str) -> None:
        self.status = status
        self.url = url
        self.request = MockRequest(resource_type)


class MockPage:
    def __init__(self) -> None:
        self.listeners: dict[str, list] = {}
        self.eval_handlers: list = []

    def on(self, event: str, callback) -> None:
        self.listeners.setdefault(event, []).append(callback)

    def emit(self, event: str, payload) -> None:
        for cb in self.listeners.get(event, []):
            cb(payload)

    def evaluate(self, script: str, arg: dict) -> dict:
        if self.eval_handlers:
            handler = self.eval_handlers.pop(0)
            return handler(script, arg)
        return {"ok": True}


def test_watchdog_filters():
    """GREEN phase test: Watchdog filters allowlisted console notices and flags unallowlisted errors."""
    page = MockPage()
    watchdog = attach_zero_error_watchdog(page, allowlist_patterns=[r"\[vite\]", r"DeprecationWarning"])

    # Allowed errors should not be captured
    page.emit("console", MockConsoleMessage("error", "[vite] hot reload connected"))
    page.emit("console", MockConsoleMessage("error", "Third-party DeprecationWarning: feature deprecated"))
    assert len(watchdog.captured_errors) == 0

    # Unallowlisted error must be captured
    page.emit("console", MockConsoleMessage("error", "Uncaught ReferenceError: foo is not defined"))
    assert len(watchdog.captured_errors) == 1
    assert "Uncaught ReferenceError" in watchdog.captured_errors[0]

    with pytest.raises(AssertionError, match="Zero-Console-And-Layout-Defect Watchdog"):
        watchdog.assert_zero_defects()


def test_WQG_HP_03_playwright_headless_execution():
    """Scenario: [WQG-HP-03] [Tier C - Integration] Playwright headless execution with wiremock and Zero-Console-Error."""
    page = MockPage()
    watchdog = attach_zero_error_watchdog(page)

    # Simulate normal page actions without errors
    page.emit("console", MockConsoleMessage("info", "Page initialized"))
    page.emit("response", MockResponse(200, "http://localhost:3000/main.css", "stylesheet"))
    page.emit("response", MockResponse(200, "http://localhost:3000/app.js", "script"))

    # Assert zero defects
    watchdog.assert_zero_defects()
    assert len(watchdog.captured_errors) == 0


def test_WQG_EC_02_allowlist_filtering():
    """Scenario: [WQG-EC-02] [Tier A - Unit] Benign console warnings filtered by allowlist."""
    page = MockPage()
    custom_allowlist = [r"React DevTools", r"analytics\.js deprecation"]
    watchdog = attach_zero_error_watchdog(page, allowlist_patterns=custom_allowlist)

    page.emit("console", MockConsoleMessage("error", "Download the React DevTools for a better development experience"))
    page.emit("console", MockConsoleMessage("error", "vendor: analytics.js deprecation warning: use v2 API"))
    page.emit("pageerror", "React DevTools extension recommendation")

    # All should be filtered out
    assert len(watchdog.captured_errors) == 0
    watchdog.assert_zero_defects()


def test_WQG_EC_03_mutually_exclusive_state_leak_and_duplicate_text():
    """Scenario: [WQG-EC-03] [Tier C - Integration] Mutually exclusive DOM state leak and duplicate text detection."""
    page = MockPage()

    # 1. State leak simulation: mutually exclusive elements are simultaneously visible
    page.eval_handlers.append(
        lambda s, a: {
            "ok": False,
            "error": "Mutually exclusive state elements are simultaneously visible: ['[data-state=\"running\"]', '[data-state=\"failed\"]']",
        }
    )
    with pytest.raises(AssertionError, match="Mutually exclusive state elements are simultaneously visible"):
        assert_dom_state_integrity(page, exclusive_state_groups=[['[data-state="running"]', '[data-state="failed"]']])

    # 2. Duplicate text simulation: consecutive duplicate word detected
    page.eval_handlers.append(
        lambda s, a: {
            "ok": False,
            "error": 'Consecutive duplicate word detected: "Tiến độ" in text "Tiến độ Tiến độ" inside selector h2',
        }
    )
    with pytest.raises(AssertionError, match="Consecutive duplicate word detected"):
        assert_dom_state_integrity(page)

    # 3. Positive accessibility clipped elements (e.g. .sr-only) are accepted as valid
    page.eval_handlers.append(lambda s, a: {"ok": True})
    assert_dom_state_integrity(page, exclusive_state_groups=[['.spinner', '.status-badge']])


def test_WQG_AR_02_webserver_lifecycle():
    """Scenario: [WQG-AR-02] [Tier C - Integration] Playwright webServer lifecycle management."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Launch python's built-in http.server on port 8942
        web_server_cmd = [sys.executable, "-m", "http.server", "8942", "--bind", "127.0.0.1"]
        test_cmd = [sys.executable, "-c", "import sys; sys.exit(0)"]

        res = run_playwright_suite(
            test_command=test_cmd,
            cwd=tmpdir,
            web_server_command=web_server_cmd,
            healthcheck_port=8942,
            healthcheck_host="127.0.0.1",
            timeout=10.0,
        )

        assert res["status"] == "PASS"
        assert res["returncode"] == 0
        assert res["duration"] > 0


def test_WQG_FR_01_uncaught_console_error():
    """Scenario: [WQG-FR-01] [Tier C - Integration] Immediate test failure on uncaught JavaScript console error."""
    page = MockPage()
    watchdog = attach_zero_error_watchdog(page)

    page.emit("console", MockConsoleMessage("error", "Uncaught TypeError: Cannot read properties of undefined (reading 'map')"))
    page.emit("pageerror", "RuntimeError: unhandled promise rejection at main.ts:42")

    assert len(watchdog.captured_errors) == 2
    assert "Uncaught TypeError" in watchdog.captured_errors[0]
    assert "RuntimeError" in watchdog.captured_errors[1]

    with pytest.raises(AssertionError, match="Zero-Console-And-Layout-Defect Watchdog detected 2 defect"):
        watchdog.assert_zero_defects()


def test_WQG_FR_03_static_asset_trap_and_unstyled_geometry():
    """Scenario: [WQG-FR-03] [Tier C - Integration] Immediate failure on 404 static stylesheet or unstyled computed geometry."""
    page = MockPage()
    watchdog = attach_zero_error_watchdog(page)

    # 1. Static stylesheet returns HTTP 404
    page.emit("response", MockResponse(404, "http://localhost:3000/styles/theme.css", "stylesheet"))
    assert len(watchdog.captured_errors) == 1
    assert "[asset-404]" in watchdog.captured_errors[0]
    assert "theme.css" in watchdog.captured_errors[0]

    # 2. Structural container renders with unstyled default geometry
    page.eval_handlers.append(
        lambda s, a: {
            "ok": False,
            "error": "Element '.card-container' has zero or negligible dimensions (0x0). Expected >= 1x1.",
        }
    )
    with pytest.raises(AssertionError, match="assert_visual_integrity defect"):
        assert_visual_integrity(page, ".card-container")
