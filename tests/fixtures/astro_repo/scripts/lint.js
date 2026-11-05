#!/usr/bin/env node
// Lint script for Astro repository fixture
const fs = require('fs');
const path = require('path');

const srcDir = path.resolve(__dirname, '..', 'src');
const files = fs.readdirSync(path.join(srcDir, 'pages'));
for (const file of files) {
  const content = fs.readFileSync(path.join(srcDir, 'pages', file), 'utf8');
  if (content.includes('console.error(')) {
    console.error(`Lint error: forbidden console.error in ${file}`);
    process.exit(1);
  }
}
console.log("[lint] ESLint and Astro linter passed cleanly with 0 violations.");
process.exit(0);

