"""Python Playwright Zero-Console-And-Layout-Defect Watchdog Fixture Companion.

Provides zero-console-error traps, static asset 404 network traps,
computed visual integrity assertions, and DOM state leak detection for Python Playwright test suites.
"""

from __future__ import annotations

import re
from typing import Any

DEFAULT_ALLOWLIST: list[str] = [
    r"\[vite\]",
    r"Lit is in dev mode",
    r"Download the React DevTools",
]


class PlaywrightZeroErrorWatchdog:
    """Watchdog that intercepts browser console errors, page crashes, and missing static assets."""

    def __init__(self, allowlist_patterns: list[str] | None = None) -> None:
        patterns = allowlist_patterns if allowlist_patterns is not None else DEFAULT_ALLOWLIST
        self.allowlist: list[re.Pattern[str]] = [re.compile(p, re.IGNORECASE) for p in patterns]
        self.captured_errors: list[str] = []

    def is_allowed(self, text: str) -> bool:
        """Check if message matches any allowlisted pattern."""
        return any(p.search(text) for p in self.allowlist)

    def handle_console(self, msg: Any) -> None:
        """Handler for page 'console' events."""
        msg_type = getattr(msg, "type", "")
        if msg_type == "error":
            text = getattr(msg, "text", str(msg))
            if not self.is_allowed(text):
                self.captured_errors.append(f"[console.error] {text}")

    def handle_pageerror(self, err: Any) -> None:
        """Handler for page 'pageerror' events."""
        text = str(err)
        if not self.is_allowed(text):
            self.captured_errors.append(f"[pageerror] {text}")

    def handle_response(self, response: Any) -> None:
        """Handler for page 'response' events (Static Asset Network Trap)."""
        try:
            req = response.request
            resource_type = req.resource_type if hasattr(req, "resource_type") else ""
            status = response.status if hasattr(response, "status") else 200
            if resource_type in ("stylesheet", "script", "font") and status >= 400:
                url = response.url if hasattr(response, "url") else "unknown"
                self.captured_errors.append(
                    f"[asset-404] Static asset failed to load ({status}): {url} [type: {resource_type}]"
                )
        except Exception as exc:  # noqa: BLE001
            self.captured_errors.append(f"[watchdog-internal-error] {exc}")

    def attach(self, page: Any) -> None:
        """Attach listeners to a Playwright page instance."""
        page.on("console", self.handle_console)
        page.on("pageerror", self.handle_pageerror)
        page.on("response", self.handle_response)

    def assert_zero_defects(self) -> None:
        """Assert no console errors, unhandled exceptions, or asset 404s were captured."""
        if self.captured_errors:
            formatted = "\n".join(f"  {idx + 1}. {err}" for idx, err in enumerate(self.captured_errors))
            raise AssertionError(
                f"Zero-Console-And-Layout-Defect Watchdog detected {len(self.captured_errors)} defect(s):\n{formatted}"
            )


def attach_zero_error_watchdog(
    page: Any,
    allowlist_patterns: list[str] | None = None,
) -> PlaywrightZeroErrorWatchdog:
    """Convenience helper to instantiate and attach the watchdog to a Playwright page."""
    watchdog = PlaywrightZeroErrorWatchdog(allowlist_patterns=allowlist_patterns)
    watchdog.attach(page)
    return watchdog


def assert_visual_integrity(
    page: Any,
    selector: str,
    options: dict[str, Any] | None = None,
) -> None:
    """Assert computed styling and layout integrity for structural UI containers."""
    opts = options or {}
    script = """
    ({ sel, opts }) => {
      const el = document.querySelector(sel);
      if (!el) {
        return { ok: false, error: `Element matching selector '${sel}' was not found in DOM.` };
      }
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);

      const isClippedA11y =
        (rect.width <= 1 && rect.height <= 1 && style.overflow === 'hidden') ||
        style.clip.includes('rect(0px, 0px, 0px, 0px)') ||
        style.clip.includes('rect(0, 0, 0, 0)') ||
        style.clipPath.includes('inset(50%)') ||
        style.clipPath.includes('inset(100%)');

      if (isClippedA11y) {
        return { ok: true, a11yClipped: true };
      }

      const minW = opts.minWidth ?? 1;
      const minH = opts.minHeight ?? 1;

      if (!opts.allowZeroDimension && (rect.width < minW || rect.height < minH)) {
        return {
          ok: false,
          error: `Element '${sel}' has zero or negligible dimensions (${rect.width}x${rect.height}). Expected >= ${minW}x${minH}.`
        };
      }

      const bg = style.backgroundColor;
      const bw = style.borderWidth;
      const pad = style.padding;
      const isUnstyledDefault =
        (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') &&
        (bw === '0px' || bw === '') &&
        (pad === '0px' || pad === '');

      return {
        ok: true,
        isUnstyledDefault,
        rect: { width: rect.width, height: rect.height },
        style: { bg, bw, pad, display: style.display }
      };
    }
    """
    result = page.evaluate(script, {"sel": selector, "opts": opts})
    if not result.get("ok"):
        raise AssertionError(f"assert_visual_integrity defect: {result.get('error')}")


def assert_dom_state_integrity(
    page: Any,
    exclusive_state_groups: list[list[str]] | None = None,
    container_selector: str = "body",
) -> None:
    """Assert DOM state integrity, mutually exclusive state elements, and detect text leaks."""
    groups = exclusive_state_groups or []
    script = """
    ({ groups, containerSel }) => {
      const container = document.querySelector(containerSel) || document.body;

      for (const group of groups) {
        const visibleSelectors = [];
        for (const sel of group) {
          const els = container.querySelectorAll(sel);
          for (const el of Array.from(els)) {
            const style = window.getComputedStyle(el);
            const rect = el.getBoundingClientRect();
            const isClippedA11y =
              (rect.width <= 1 && rect.height <= 1 && style.overflow === 'hidden') ||
              style.clip.includes('rect(0px, 0px, 0px, 0px)') ||
              style.clip.includes('rect(0, 0, 0, 0)') ||
              style.clipPath.includes('inset(50%)') ||
              style.clipPath.includes('inset(100%)');

            const isVisible =
              !isClippedA11y &&
              style.display !== 'none' &&
              style.visibility !== 'hidden' &&
              parseFloat(style.opacity || '1') > 0 &&
              rect.width > 0 &&
              rect.height > 0;

            if (isVisible) {
              visibleSelectors.push(sel);
              break;
            }
          }
        }
        if (visibleSelectors.length > 1) {
          return {
            ok: false,
            error: `Mutually exclusive state elements are simultaneously visible: [${visibleSelectors.join(', ')}] in group [${group.join(', ')}]`
          };
        }
      }

      const textNodes = container.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"], [data-card-title]');
      for (const el of Array.from(textNodes)) {
        const text = (el.textContent || '').trim().replace(/\\s+/g, ' ');
        const words = text.split(' ');
        for (let i = 0; i < words.length - 1; i++) {
          if (words[i].length >= 4 && words[i].toLowerCase() === words[i + 1].toLowerCase()) {
            return {
              ok: false,
              error: `Consecutive duplicate word detected: "${words[i]}" in text "${text}" inside selector ${el.tagName.toLowerCase()}`
            };
          }
        }
      }

      return { ok: true };
    }
    """
    result = page.evaluate(script, {"groups": groups, "containerSel": container_selector})
    if not result.get("ok"):
        raise AssertionError(f"assert_dom_state_integrity defect: {result.get('error')}")
