# Release Notes: d3nexus v1.27.0

**Release Date:** November 09, 2026  
**Version:** `1.27.0`  
**Git Tag:** `v1.27.0`, `d3nexus--v1.27.0`

---

## Executive Summary

`v1.27.0` establishes official native runtime support for **Kiro CLI** via Kiro powers (`kiro-cli powers install`), delivers a comprehensive header and visual overhaul to the **AI Quota Dashboard** (inline server address and sync indicators, quick-select "Tất cả" filter button, duplicate tag elimination), introduces **Anthropic Live OAuth API Polling** for Claude Code usage, and hardens profile isolation to prevent AI Provider cards from being shadowed by ghost profiles in `antigravity_homes/`.

---

## Key Highlights

### 1. Official Kiro CLI Native Power Support
- **4th Official AI Runtime**: Designates Kiro CLI alongside Antigravity, Claude Code, and OpenAI Codex as a first-class supported platform.
- **Native Power Distribution**: Installable directly with a single command:
  ```bash
  kiro-cli powers install https://github.com/DanhDue/ai-agent-tools.git
  ```
  or locally during development:
  ```bash
  kiro-cli powers install .
  ```
- **Unified Single Source of Truth**: Reuses root `plugin.json` and `AGENTS.md` steering guidelines without duplication or configuration drift.
- **Automated Sync**: Release automation in `scripts/release.sh` now automatically refreshes local Kiro powers on release publish.

### 2. AI Quota Dashboard Header & UX Overhaul
- **Multi-Agent Identity**: Rebranded from "Antigravity Quota Dashboard" to **AI Quota Dashboard** across header title, browser tab title, and desktop notifications.
- **Aligned Status Bar**: Promotes fixed indicators (`● Live Server (127.0.0.1:8765)` and `● Đồng bộ ...m trước`) to Row 1 alongside the title, maximizing vertical content space.
- **Decluttered Interface**: Eliminates duplicate active profile tags and redundant percentage badges from the header.
- **Quick-Select "Tất cả" Filter**: Adds a dedicated `● Tất cả (26)` quick-filter button (`statBtnAll`) at the start of Row 2 with glowing cyan active ring indicators (`ring-2 ring-sky-400 bg-sky-500/30`).
- **Kiro CLI Action Streamlining**: Direct terminal launch via `kiro-cli` and removal of non-applicable Argon activation and recurring scheduler buttons from the monthly credit pool card.

### 3. Claude Code Anthropic Live OAuth Usage Polling
- **Direct API Verification**: Upgrades Claude Code quota provider to poll Anthropic's OAuth API (`/v1/oauth/claude_cli/usage`) using macOS Keychain credentials or `~/.claude.json`.
- **Live Metrics**: Accurately tracks 5-hour rolling session token usage and 7-day rate limit thresholds in real time.
- **Resilient Fallback**: Gracefully degrades to local JSON cache when offline or when tokens expire.

### 4. Profile Isolation & Ghost Provider Exclusion
- **Ghost Directory Defense**: Filters out known AI Provider names (`kiro`, `claude`, `codex`) in `get_all_profiles()`, preventing accidental directories under `antigravity_homes/` from registering as Antigravity profiles.
- **Provider Integrity Guard**: Strengthens `format_profile_for_dashboard()` to ensure AI Provider cards are never overwritten with "Auth Needed" states during background scans.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh`: 🟢 **PASS — safe to publish** (Sections 1–17, all 41 test suites green)
- `tests/test_kiro_quota.py`: 🟢 **PASS** (7/7 unit tests passing)
- `tests/test_agy_quota.py`: 🟢 **PASS** (9/9 unit tests passing)
