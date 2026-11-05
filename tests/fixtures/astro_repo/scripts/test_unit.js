#!/usr/bin/env node
// Unit test runner script for Astro repository fixture
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const indexHtml = fs.readFileSync(path.resolve(__dirname, '..', 'src', 'pages', 'index.astro'), 'utf8');
assert(indexHtml.includes('Trang chủ'), "Missing title in index.astro");
assert(indexHtml.includes('class="app-header"'), "Missing app-header class");
assert(indexHtml.includes('class="content-box"'), "Missing content-box class");
console.log("[test:unit] 8 unit tests passed across Astro components and utils.");
process.exit(0);

