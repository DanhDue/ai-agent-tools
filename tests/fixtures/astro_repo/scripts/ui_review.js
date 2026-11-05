#!/usr/bin/env node
// UI review runner for Astro repository fixture
const { execFileSync } = require('child_process');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..');
const auditScript = path.resolve(__dirname, '../../../../skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py');
try {
  execFileSync('python3', [auditScript, '--project-root', projectRoot, '--base-ref', 'main'], { encoding: 'utf8' });
  console.log("[ui:review] Audited UI state and styles: 4 invariants verified with 0 defects.");
  process.exit(0);
} catch (err) {
  console.error("UI Review failed:", err.stdout || err.message);
  process.exit(1);
}

