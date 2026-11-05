import { test as base, expect, Page, Locator } from '@playwright/test';

export interface WatchdogOptions {
  consoleErrorAllowlist?: RegExp[];
  exclusiveStateSelectors?: string[][];
  trapStaticAssets?: boolean;
}

export interface VisualIntegrityOptions {
  allowZeroDimension?: boolean;
  minWidth?: number;
  minHeight?: number;
}

/**
 * Checks if an element is an intentionally clipped accessibility element (e.g., .sr-only).
 */
export function isAccessibilityClipped(computedStyle: CSSStyleDeclaration, rect: DOMRect): boolean {
  if (rect.width <= 1 && rect.height <= 1 && computedStyle.overflow === 'hidden') {
    return true;
  }
  const clip = computedStyle.clip || '';
  if (clip.includes('rect(0px, 0px, 0px, 0px)') || clip.includes('rect(0, 0, 0, 0)')) {
    return true;
  }
  const clipPath = computedStyle.clipPath || '';
  if (clipPath.includes('inset(50%)') || clipPath.includes('inset(100%)')) {
    return true;
  }
  return false;
}

/**
 * Asserts computed style and geometry integrity for structural UI containers.
 */
export async function assertVisualIntegrity(
  page: Page,
  selector: string,
  options: VisualIntegrityOptions = {}
): Promise<void> {
  const result = await page.evaluate(
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
          error: `Element '${sel}' has zero or negligible dimensions (${rect.width}x${rect.height}). Expected >= ${minW}x${minH}.`,
        };
      }

      // Check default unstyled computed styling: transparent bg, 0px border, 0px padding
      const bg = style.backgroundColor;
      const bw = style.borderWidth;
      const pad = style.padding;
      const isUnstyledDefault =
        (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') &&
        (bw === '0px' || bw === '') &&
        (pad === '0px' || pad === '');

      if (isUnstyledDefault) {
        return {
          ok: false,
          error: `Element '${sel}' renders with unstyled default styles (transparent background, 0px border, 0px padding).`,
        };
      }

      return {
        ok: true,
        isUnstyledDefault,
        rect: { width: rect.width, height: rect.height },
        style: { bg, bw, pad, display: style.display },
      };
    },
    { sel: selector, opts: options }
  );

  if (!result.ok) {
    throw new Error(`assertVisualIntegrity defect: ${result.error}`);
  }
}

/**
 * Asserts DOM state integrity and detects duplicate text leaks.
 */
export async function assertDomStateIntegrity(
  page: Page,
  exclusiveStateGroups: string[][] = [],
  containerSelector: string = 'body'
): Promise<void> {
  const result = await page.evaluate(
    ({ groups, containerSel }) => {
      const container = document.querySelector(containerSel) || document.body;

      function isElementClippedOrInvisible(element: Element): boolean {
        let curr: Element | null = element;
        while (curr && curr !== document.documentElement) {
          const s = window.getComputedStyle(curr);
          if (s.display === 'none' || s.visibility === 'hidden' || s.visibility === 'collapse' || parseFloat(s.opacity || '1') === 0) {
            return true;
          }
          if (s.clip && (s.clip.includes('rect(0px, 0px, 0px, 0px)') || s.clip.includes('rect(0, 0, 0, 0)') || s.clip.includes('rect(1px, 1px, 1px, 1px)'))) {
            return true;
          }
          if (s.clipPath && (s.clipPath.includes('inset(50%)') || s.clipPath.includes('inset(100%)'))) {
            return true;
          }
          if (typeof curr.getBoundingClientRect === 'function') {
            const r = curr.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) {
              return true;
            }
            if ((s.overflow === 'hidden' || s.overflowX === 'hidden' || s.overflowY === 'hidden') && (r.width <= 1 || r.height <= 1)) {
              return true;
            }
          }
          curr = curr.parentElement;
        }
        return false;
      }

      function isNodeVisible(element: Element): boolean {
        if (!element) return false;
        return !isElementClippedOrInvisible(element);
      }

      function getVisibleText(node: Node | null): string {
        if (!node) return '';
        if (node.nodeType === 3) {
          return node.nodeValue || '';
        }
        if (node.nodeType === 1) {
          const el = node as Element;
          if (isElementClippedOrInvisible(el)) {
            return '';
          }
          let text = '';
          const children = Array.from(el.childNodes);
          for (const child of children) {
            text += getVisibleText(child);
          }
          return text;
        }
        return '';
      }

      // 1. Check mutually exclusive state selectors
      for (const group of groups) {
        const visibleSelectors: string[] = [];
        for (const sel of group) {
          const els = container.querySelectorAll(sel);
          for (const el of Array.from(els)) {
            if (isNodeVisible(el)) {
              visibleSelectors.push(sel);
              break;
            }
          }
        }
        if (visibleSelectors.length > 1) {
          return {
            ok: false,
            error: `Mutually exclusive state elements are simultaneously visible: [${visibleSelectors.join(', ')}] in group [${group.join(', ')}]`,
          };
        }
      }

      // 2. Check consecutive duplicate substring rendering inside headings/titles
      const textNodes = container.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"], [data-card-title]');
      for (const el of Array.from(textNodes)) {
        if (!isNodeVisible(el)) continue;

        const text = (getVisibleText(el) || '').trim().replace(/\s+/g, ' ');
        // Check for adjacent duplicate words/phrases of 2+ characters, e.g. "Tiến độ Tiến độ"
        const dupMatch = text.match(/(?:^|\s)([A-Za-zÀ-ỹ0-9_]{2,}(?:\s+[A-Za-zÀ-ỹ0-9_]{2,})*)\s+\1(?:$|\s|[.,;])/i);
        if (dupMatch) {
          return {
            ok: false,
            error: `Consecutive duplicate phrase detected: "${dupMatch[1]}" in text "${text}" inside selector ${el.tagName.toLowerCase()}`,
          };
        }
      }

      return { ok: true };
    },
    { groups: exclusiveStateGroups, containerSel: containerSelector }
  );

  if (!result.ok) {
    throw new Error(`assertDomStateIntegrity defect: ${result.error}`);
  }
}

/**
 * Extended Playwright test fixture attaching Zero-Console-And-Layout-Defect Watchdog.
 */
export const test = base.extend<{ watchdog: void }>({
  watchdog: [
    async ({ page }, use, testInfo) => {
      const capturedErrors: string[] = [];
      const allowlist: RegExp[] = [
        /\[vite\]/i,
        /Lit is in dev mode/i,
        /Download the React DevTools/i,
      ];

      // Read custom allowlist patterns from manifest or env
      try {
        const fs = require('fs');
        const path = require('path');
        const manifestPath = path.resolve('.agents/quality/web-quality.json');
        if (fs.existsSync(manifestPath)) {
          const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
          if (Array.isArray(manifest.console_error_allowlist)) {
            for (const p of manifest.console_error_allowlist) {
              allowlist.push(new RegExp(p, 'i'));
            }
          }
        }
      } catch (_) {}
      if (process.env.CONSOLE_ERROR_ALLOWLIST) {
        for (const p of process.env.CONSOLE_ERROR_ALLOWLIST.split(',')) {
          if (p.trim()) allowlist.push(new RegExp(p.trim(), 'i'));
        }
      }

      // Console error listener
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          const text = msg.text();
          const isAllowed = allowlist.some((re) => re.test(text));
          if (!isAllowed) {
            capturedErrors.push(`[console.error] ${text}`);
          }
        }
      });

      // Page runtime exception listener
      page.on('pageerror', (err) => {
        const text = err.message || String(err);
        const isAllowed = allowlist.some((re) => re.test(text));
        if (!isAllowed) {
          capturedErrors.push(`[pageerror] ${text}\nStack: ${err.stack || 'no stack'}`);
        }
      });

      // Static Asset Network Trap
      page.on('response', (response) => {
        const req = response.request();
        const type = req.resourceType();
        if (['stylesheet', 'script', 'font'].includes(type) && response.status() >= 400) {
          capturedErrors.push(
            `[asset-404] Static asset failed to load (${response.status()}): ${response.url()} [type: ${type}]`
          );
        }
      });

      await use();

      if (capturedErrors.length > 0) {
        throw new Error(
          `Zero-Console-And-Layout-Defect Watchdog detected ${capturedErrors.length} defect(s):\n` +
            capturedErrors.map((e, idx) => `  ${idx + 1}. ${e}`).join('\n')
        );
      }
    },
    { auto: true },
  ],
});

export { expect };
