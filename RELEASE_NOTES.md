# Release Notes: d3nexus v1.35.2

**Release Date:** November 26, 2026  
**Version:** `1.35.2`  
**Git Tag:** `v1.35.2`, `d3nexus--v1.35.2`

---

## Executive Summary

`v1.35.2` fixes broken clipboard copy buttons in the Check-Quota **Account Info** modal (Copy Email, Copy CLI Command, and Login CLI Command) both standalone and when embedded inside the Tasks Dashboard iframe.

---

## Key Highlights

### Reliable Clipboard Copy Across Standalone & Embedded Quota UI (`skills/check-quota/`, `skills/check-tasks/`)
- **Iframe Permissions**: Added `allow="clipboard-write; clipboard-read"` to `#quota-iframe` in `tasks_dashboard.html` so cross-origin embedded Quota views are not blocked by browser Permissions Policy.
- **Automatic Fallback**: Unified `copyInfoEmail()`, `copyInfoCliCmd()`, `copyLoginCmd()`, and `copyProfileNameToClipboard()` behind `copyTextToClipboard()` with automatic `textarea` + `document.execCommand("copy")` fallback and clear toast confirmation.

---

## Verifications & Quality Gates Passed

- `python3 -m pytest tests/test_cqra_quota_ui.py tests/test_rsdh_quota_modal_stack.py -q` (16/16 passed)
- `bash scripts/verify.sh --quiet` (all structural integrity checks & 90 test suites across 14 parallel workers: PASS)
