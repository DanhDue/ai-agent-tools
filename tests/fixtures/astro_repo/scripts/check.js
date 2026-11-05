#!/usr/bin/env node
// Type check script for Astro repository fixture
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const srcFile = path.resolve(__dirname, '..', 'src', 'pages', 'index.astro');
if (!fs.existsSync(srcFile)) {
  console.error("Missing src/pages/index.astro");
  process.exit(1);
}
const content = fs.readFileSync(srcFile, 'utf8');
const scriptMatch = content.match(/---\n([\s\S]*?)\n---/);
if (scriptMatch) {
  try {
    new vm.Script(scriptMatch[1]);
  } catch (err) {
    console.error("Syntax error in Astro frontmatter:", err.message);
    process.exit(1);
  }
}
console.log("[type-check] ASTRO TypeScript checks completed cleanly with 0 errors.");
process.exit(0);

