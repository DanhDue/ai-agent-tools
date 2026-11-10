# Release Notes: d3nexus v1.28.1

**Release Date:** November 10, 2026  
**Version:** `1.28.1`  
**Git Tag:** `v1.28.1`, `d3nexus--v1.28.1`

---

## Executive Summary

`v1.28.1` switches Antigravity profile session pre-warming and scheduling to Claude 5.5 Sonnet (`claude-sonnet-5-5-low`) instead of the default Gemini model, introduces the **Argon Profiles** interactive quick access filter badge to the Quota Dashboard, and cleans up redundant drawer content.

---

## Key Highlights

### 1. Claude 5.5 Pre-Warming & Scheduled Activation for Antigravity Profiles
- **Direct Claude Activation**: Replaces default Gemini ping (`agy -p ...`) with `--model claude-sonnet-5-5-low` in `skills/refresh-session/resources/scripts/refresh_session.py` (`ping_profile`) and `scripts/agy_quota.py` (`execute_ping_profile`).
- **5-Hour Rolling Rate-Limit Pre-Warm**: Automatically initializes the rolling 5-hour quota window for Claude 5.5 / GPT models inside Antigravity profiles when executing on-demand pings or scheduled daily background daemons (`/refresh-session schedule`).
- **Preserved Argon Entitlement**: Preserves 7-day weekly Argon activation when entitled, applying humanized anti-bot jitter between model calls.

### 2. Argon Profiles Quick Access Filter Badge
- **One-Click Filtering**: Adds `• Argon Profiles` badge to the top statistics bar of the Quota Dashboard, next to `Active Profiles`.
- **Dynamic Badge & Count**: Calculates active Argon support across all non-provider profiles (12 active Argon profiles) and synchronizes with the `#statusFilter` dropdown and URL search params (`?status=ARGON`).
- **Toggle Action**: Clicking the badge filters to show exclusively Argon profiles; clicking it again resets to "Tất cả".

### 3. Dashboard UI Streamlining
- **Removed TypeScript Contract Drawer**: Removes the redundant static specification drawer from the bottom of `quota_dashboard.html` for a clean, distraction-free view.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh`: 🟢 **PASS — safe to publish**
- `test_refresh_session.py` & `test_agy_quota.py`: 🟢 **PASS** (53/53 unit tests passing)
- `test_lifecycle_document_contract.py` & `test_verifiable_handoff_text.py`: 🟢 **PASS** (26/26 contract tests passing)
